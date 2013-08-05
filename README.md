Performance Monitoring Tool
===========================

About
-----

Web based tool built to monitor the front-end performances of websites. This version is based on webpagetest.org API.

You will need an API key to use it.

Requirements
------------

* MongoDB >= 2.2
* PHP >= 5.3.2 (and extensions: mongo)
* Python (and libs: pika, pymongo)
* RabbitMQ
* Apache

Installation
------------

Extract the code inside any directory that can be accessed by apache (configure your vhost accordingly to point to the web/ folder)

After installing all the required libraries, make sure all the services are running (MongoDB, Apache, PHP, RabbitMQ)

Open your web browser and go to this url

    /app.php/perf/time
