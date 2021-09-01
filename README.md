iNELS InfluxDB
===

This project handles the saving of home automation events from the proprietary [iNELS home automation suite](https://www.inels.com/). It parses events then saves them to an [InfluxDB](https://www.influxdata.com/) database which then can be displayed using data monitoring tools such as [Grafana](https://grafana.com/).

How to run
===

Docker and Docker Compose should be installed on the machine before proceeding.

Steps to start the inels-influxdb container:

- Clone this repository to the system
  - `git clone https://github.com/domenix/inels-influxdb.git`
- Change into the directory that was downloaded
  - `cd inels-influxdb`
- Rename example.env file to .env
  - `mv example.env`
- Edit the properties inside .env according to your preference, keep in mind that `DB_TOKEN` should be something secure
- Start the container
  - `docker-compose up -d`

Steps to start InfluxDB and Grafana:

- Change into the `monitoring` directory
  - `cd monitoring`
- Rename example.env file to .env
  - `mv example.env`
- Edit the properties inside .env according to your preference, `DOCKER_INFLUXDB_INIT_ADMIN_TOKEN` should match `DB_TOKEN` that was set previously
- Start the containers
  - `docker-compose up -d`

If done correctly, InfluxDB should be accessible on the machine on port 8086 and the defined bucket should have some data already in it. Access Grafana on port 3000 and makes some cool looking dashboards for your home automation system. Enjoy!

Troubleshooting
===

You can see the logs of the container by using `docker-compose logs --follow`. It will watch the logs of all services defined in the docker-compose.yml file present in the current directory. Use `docker-compose logs --follow inels-influxdb` in order to follow one specific service or execute `docker logs inels-influxdb` in any directory of your system.


Todo
===
- Queue up events in the database thread if the db server becomes unavailable.
- Database error handling should be better compartmentalized (right now errors are just printed out from the influxdb-client library) and connection loss during saving should be handled as well similarly to the connection thread.
<!-- 
[![buy me a coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/domenix) -->

<!-- <div align="center"><div>

<p align="center">
  <img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" href=https://www.buymeacoffee.com/domenix>
</p> -->

<div>
<a href="https://www.buymeacoffee.com/domenix">
  <img align="center" src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png">
</a>
</div>

<!-- <p align="center">centered text</p> -->