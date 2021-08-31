iNELS InfluxDB
===

This project handles events of the proprietary [iNELS home automation suite](https://www.inels.com/). It parses events then saves them to an [InfluxDB](https://www.influxdata.com/) database which then can be displayed using data monitoring tools such as [Grafana](https://grafana.com/).


Todo
===
- Queue up events in the database thread if the db server becomes unavailable.
- Database error handling should be better compartmentalized (right now errors are just printed out from the influxdb-client library) and connection loss during saving should be handled as well similarly to the connection thread.

[![buy me a coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/domenix)
