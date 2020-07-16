# Adding publications from other centers to THREDDS/ERDDAP/CSW for portal ingestion

1. Obtain data from ScienceBase or St. Pete Data Release server
   1. End result should be a directory of .nc files
   1. Can do this locally or e.g. on Pangeo CHS JupyterLab
1. Create Jupyter Notebook to process from EPIC to CF. See [process_F73R0R07.ipynb](https://github.com/dnowacki-usgs/cmhrp-portal/blob/master/process_F73R0R07.ipynb) for an example
   1. You should have CF-compliant netCDF files in a new directory, e.g., `clean`
1. Get the data to gamone
   1. Multiple ways to do this. One is to FTP files to ftpint/ftpext, and then download the files onto gamone.
   1. Recommend something like `wget -w 10 -bqc -i urls.txt` where `urls.txt` is a list of `ftp://ftpint.usgs.gov...` URLs.
1. Put data in a directory discoverable by THREDDS on gamone
   1. e.g., under `/sand/usgs/users/<username>/doi-<DOI SNIPPET>`, where `<DOI SNIPPET>` is the last part of the doi; the stuff after the trailing slash in `doi:10.5066/F73R0R07`. In this case it's `F73R0R07`.
1. Create ERDDAP XML snippets
   1. Use [make_erddap.py](https://github.com/dnowacki-usgs/cmhrp-portal/blob/master/make_erddap.py) to generate a shell script to run from within the ERDDAP Docker container. Run the script as `python make_erddap.py <DOI SNIPPET>`. This will generate the file `edout.sh`.
   1. Put this file somewhere accessible from the container (e.g., `/opt/docker/erddap/data`)
   1. Log in to the container `docker exec -it erddap bash` and run the script (`bash /erddapData/edout.sh`) from the directory where `GenerateDatasetsXml.sh` lives (`/usr/local/tomcat/webapps/erddap/WEB-INF`)
   1. Copy the newly created .xml files from `/opt/docker/erddap/data/logs` to your xml snippet directory (e.g., `/opt/docker/erddap/xml_parts/dan/`)
   1. Replace the randomly generated datasetID with a datasetID based on the filename using [make_datasetID.sh](https://github.com/dnowacki-usgs/cmhrp-portal/blob/master/make_datasetID.sh): `./make_datasetID.sh ELW*.xml` or similar; put the appropriate glob for your filenames as an argument to the shell script.
1. Update ERDDAP `datasets.xml`
   1. `cd /opt/docker/erddap`
   1. `bash do_cat`
1. Add data to the CSW
   1. Add the THREDDS catalog URL to [get_ts_iso.py](https://github.com/USGS-CMG/usgs-cmg-portal/blob/master/catalog_harvest/get_ts_iso.py).
   1. `conda activate IOOS`
   1. `sudo python get_ts_iso.py`
   1. After allowing an hour or two for the CSW to harvest, check for your new dataset using [test_csw.py](https://github.com/dnowacki-usgs/cmhrp-portal/blob/master/test_csw.py)

# doi:10.5066/F7VD6XBF

`./run_all_spcmsc.sh`
`cd files/clean/ && scp *nc gamone.whoi.edu:/sand/usgs/users/dnowacki/doi-F7VD6XBF/ && cd ../..`


# doi:10.5066/F71C1W36

`./run_all_pcmsc_nmb.sh`
`cd pcmsc/NMBTimeSeriesData/clean/ && scp *nc gamone.whoi.edu:/sand/usgs/users/dnowacki/doi-F71C1W36/ && cd ../../..`
