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

### file_operations in the target module (char & block)

There are several definitions in `module_init`

#### 1. register_xxxdev in old kernel (< 2.5.70)

```c
// for char device
int register_chrdev(unsigned int major, const char * name, struct file_operations *fops);
```

#### 2. cdev_init in newer kernel (>= 2.5.70)

```c
// for char device
void cdev_init(struct cdev *cdev, const struct file_operations *fops)
```



### struct file_operations offset

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

