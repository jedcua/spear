# System for Plate Evaluation, Assessment, and Recognition [SPEAR] #

![Screenshot 1](/screenshots/lpr1.png?raw=true)
![Screenshot 2](/screenshots/lpr2.png?raw=true)

## Introduction ##
License Plate Recognition system developed as an output of our 
undergraduate thesis written in Python.

It features reading the alphanumeric code from a license plate and
performing a database lookup for evaluating possible violations
related to that license plate.

The database lookup currently checks for the following:

   * Unregistered plates
   * Expired plates
   * Wanted/Reported plates
   * Stolen plates

## Requirements ##
SPEAR is written in Python version 2.7.8.

The following Python libraries are required:

    * SimpleCV
    * openCV
    * matplotlib.pyplot
    * numpy
    * texttable
    * termcolor
    * pymysql
