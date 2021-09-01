Example
===

This folder contains docker-compose configuration for Grafana and InfluxDB. It uses the same network as inels-influxdb therefore they will be able to access each other.

How to backup volumes
===

Make a backup of InfluxDB and Grafana on the computer.

Steps:

- Open a terminal and SSH into the system
- Change into this directory
- Ensure that Grafana and InfluxDB are shut down
  - Execute: `docker-compose stop grafana influxdb`
- Execute the commands below to make a backup of the volumes:
  - `sudo docker run --rm --volumes-from grafana -v $(pwd)/backup:/backup ubuntu tar cvf /backup/grafana_backup.tar /var/lib/grafana`
  - `sudo docker run --rm --volumes-from influxdb -v $(pwd)/backup:/backup ubuntu tar cvf /backup/influxdb_backup.tar /var/lib/influxdb2`
- The two volumes are now backed up into tar files in this directory
- Copy these tar files to somewhere safe

How to restore volumes
===

- Open a terminal and SSH into the system
- Change into this directory
- Copy the tar files that were created in the backup process into this directory
- **On a new machine**: If Grafana and InfluxDB were NEVER run before on this machine, execute the following before proceeding (in order to ensure that the volumes we are trying to overwrite exist already):
  - `docker-compose up -d`
- Execute the following command to ensure that Grafana and InfluxDB are shut down
  - `docker-compose stop grafana influxdb`
- Execute the commands below to overwrite the volumes:
  - `sudo docker run --rm --volumes-from grafana -v $(pwd)/backup:/backup ubuntu bash -c "cd / && tar xvf /backup/grafana_backup.tar"`
  - `sudo docker run --rm --volumes-from influxdb -v $(pwd)/backup:/backup ubuntu bash -c "cd / && tar xvf /backup/influxdb_backup.tar"`
- The two volumes are now restored and the tar files can be deleted