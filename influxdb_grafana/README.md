Example
===

This folder contains docker-compose configuration for Grafana and InfluxDB. It uses the same network as inels-influxdb therefore they will be able to access each other.

How to back up volumes
===

docker run --rm --volumes-from grafana -v $(pwd):/backup ubuntu tar cvf /backup/grafana_backup.tar /var/lib/grafana

docker run --rm --volumes-from influxdb -v $(pwd):/backup ubuntu tar cvf /backup/influxdb_backup.tar /var/lib/influxdb2

How to restore volumes
===

docker run --rm --volumes-from grafana -v $(pwd):/backup ubuntu bash -c "cd / && tar xvf /backup/grafana_backup.tar"

docker run --rm --volumes-from influxdb -v $(pwd):/backup ubuntu bash -c "cd / && tar xvf /backup/influxdb_backup.tar"