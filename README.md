# FopsFinder

A simple tool for file_operations finding in linux kernel

## How to install

You need IDA pro which can run ida python scripts. (Only IDA pro 9.4sp1 was tested)

Run `uv sync` to create virtual python environment.

## How to use

You need to get the *.i64 database first.

Run the following command:
```bash
python main.py -k /the/path/to/kernel.i64
```

## How it works

### file_operations

#### file_operations in the target module

file_operations is usually used in char / procfs / misc devices
There are several definitions in `module_init`

##### 1. register_xxxdev in old kernel (< 2.5.70)

```c
// for char device
int register_chrdev(unsigned int major, const char * name, struct file_operations *fops);
```

##### 2. cdev_init in newer kernel (>= 2.5.70)

```c
// for char device
void cdev_init(struct cdev *cdev, const struct file_operations *fops)
```

#### struct file_operations offset

By accessing the `struct file_operations tty_fops`, we can get the exact file_operations offset.

The definition of tty_fops:
```c
static struct file_operations tty_fops = {
	.llseek		= no_llseek,
	.read		= tty_read,
	.write		= tty_write,
	.poll		= tty_poll,
	.ioctl		= tty_ioctl,
	.open		= tty_open,
	.release	= tty_release,
	.fasync		= tty_fasync,
};
```
So we can get `open`/`read`/`write`/`ioctl`'s offset of struct file_operations.

1. in old kernel (< 2.5.70)
```c
/*
 * Called by a tty driver to register itself.
 */
int tty_register_driver(struct tty_driver *driver)
{
	int error;
        int i;

	if (driver->flags & TTY_DRIVER_INSTALLED)
		return 0;

	error = register_chrdev(driver->major, driver->name, &tty_fops);
	if (error < 0)
		return error;
	else if(driver->major == 0)
		driver->major = error;

	if (!driver->put_char)
		driver->put_char = tty_default_put_char;
	
	list_add(&driver->tty_drivers, &tty_drivers);
	
	if ( !(driver->flags & TTY_DRIVER_NO_DEVFS) ) {
		for(i = 0; i < driver->num; i++)
		    tty_register_device(driver, driver->minor_start + i);
	}
	proc_tty_register_driver(driver);
	return error;
}
```
we can retrieve the file_operations struct from `register_chrdev()`

2. in newer kernel (>= 2.5.70)
```c
/*
 * Ok, now we can initialize the rest of the tty devices and can count
 * on memory allocations, interrupts etc..
 */
int __init tty_init(void)
{
	register_sysctl_init("dev/tty", tty_table);
	cdev_init(&tty_cdev, &tty_fops);
	if (cdev_add(&tty_cdev, MKDEV(TTYAUX_MAJOR, 0), 1) ||
	    register_chrdev_region(MKDEV(TTYAUX_MAJOR, 0), 1, "/dev/tty") < 0)
		panic("Couldn't register /dev/tty driver\n");
	device_create(&tty_class, NULL, MKDEV(TTYAUX_MAJOR, 0), NULL, "tty");

	cdev_init(&console_cdev, &console_fops);
	if (cdev_add(&console_cdev, MKDEV(TTYAUX_MAJOR, 1), 1) ||
	    register_chrdev_region(MKDEV(TTYAUX_MAJOR, 1), 1, "/dev/console") < 0)
		panic("Couldn't register /dev/console driver\n");
	consdev = device_create_with_groups(&tty_class, NULL,
					    MKDEV(TTYAUX_MAJOR, 1), NULL,
					    cons_dev_groups, "console");
	if (IS_ERR(consdev))
		consdev = NULL;

#ifdef CONFIG_VT
	vty_init(&console_fops);
#endif
	return 0;
}
```
We can retrieve the file_operations struct from `cdev_init()`

### TODO: block_device_operations

#### In newer kernel (>= 2.5.65)
block_device_operations is used in block devices
For blkdev, we only consider the open/release/ioctl syscall.

The target blkdev is loop.
The `lo_fops` struct(In kernel 4.19.151): 
```c
static const struct block_device_operations lo_fops = {
	.owner =	THIS_MODULE,
	.open =		lo_open,
	.release =	lo_release,
	.ioctl =	lo_ioctl,
#ifdef CONFIG_COMPAT
	.compat_ioctl =	lo_compat_ioctl,
#endif
};
```

And lo_fops is referenced in `loop_add`(In kernel 4.19.151):
```c
static int loop_add(struct loop_device **l, int i)
{
	struct loop_device *lo;
	struct gendisk *disk;
  ...
	disk->flags |= GENHD_FL_EXT_DEVT;
	atomic_set(&lo->lo_refcnt, 0);
	lo->lo_number		= i;
	spin_lock_init(&lo->lo_lock);
	disk->major		= LOOP_MAJOR;
	disk->first_minor	= i << part_shift;
	disk->fops		= &lo_fops;
	disk->private_data	= lo;
	disk->queue		= lo->lo_queue;
	sprintf(disk->disk_name, "loop%d", i);
	add_disk(disk);
	*l = lo;
	return lo->lo_number;
  ...
}
```
But cuz the offset is possibly changed among the kernel's version, we should not locate fops child by hard-coding.
In vmlinux kernel, the `lo_open`/`lo_release`/`lo_ioctl` funcs is only referenced in lo_fops. So we can get the referenced address, then traverse the address up to find the first defined global var. Then we need to validate it in `loop_add`, after which can we tell the target global var is `lo_fops`, then we can get the definition.

#### In older kernel (2.3.37 - 2.5.64)
In older kernel version, the blkdev is registered with `register_blkdev`
```c
int register_blkdev(unsigned int major, const char * name, struct block_device_operations *bdops)
{
	if (devfs_only())
		return 0;
	if (major == 0) {
		for (major = MAX_BLKDEV-1; major > 0; major--) {
			if (blkdevs[major] == NULL) {
				blkdevs[major] = name;
				return major;
			}
		}
		return -EBUSY;
	}
	if (major >= MAX_BLKDEV)
		return -EINVAL;
	if (blkdevs[major])
		return -EBUSY;
	blkdevs[major] = name;
	return 0;
}
```
And the `loop_init` and `lo_open` are also defined, so we can still use the newer method.

#### In Even older kernel (<= 2.3.36)
In even older kernel version, the blkdev is registered with `register_blkdev`
```c
int register_blkdev(unsigned int major, const char * name, struct file_operations *fops)
{
	if (major >= MAX_BLKDEV)
		return -EINVAL;
	if (blkdevs[major].fops)
		return -EBUSY;
	blkdevs[major].name = name;
	blkdevs[major].fops = fops;
	return 0;
}
```
So there is the same fops struct with char device.

### seq_operations

seq_operations is often used in procfs devices
While in all linux versions' code, the definition is the same:
```c
struct seq_operations {
	void * (*start) (struct seq_file *m, loff_t *pos);
	void (*stop) (struct seq_file *m, void *v);
	void * (*next) (struct seq_file *m, void *v, loff_t *pos);
	int (*show) (struct seq_file *m, void *v);
};
```

