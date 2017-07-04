# dtools

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Tools for downloading and preparing datasets.

## Usage

* Install [Node.py] with `pip3 install node.py`
* Install dependencies with `nppm3 install` from inside the dtools directory
* Run any script as `nodepy3 <path/to/script>`

  [Node.py]: https://nodepy.org/

## NASA Exoplanet Archive

The [NASA Exoplanet Archive][0] offers bulk data downloads which actually only
provides scripts for the bulk-download that in turn use `wget`. If you don't
have `wget` installed or you simply want to extract all URLs instead of
downloading them, this is where *dtools* comes in handy.

For example, you can download the KELT timeseries data from [here][1] (in
[IPAC Table Format] which can be read by [astropy]), extract the `.bat` files
and pass them to the script to extract the download URLs, or download them
immediately.

__Extract URLs__

    niklas@lx1 ~/repos/dtools
    $ nodepy3 nasa/exoplanetarchive extract-urls KELT_N*_wget.bat
    http://exoplanetarchive.ipac.caltech.edu:80/data/ETSS//KELT2/005/055/28/KELT_N02_lc_000001_V01_east_raw_lc.tbl
    http://exoplanetarchive.ipac.caltech.edu:80/data/ETSS//KELT2/005/055/73/KELT_N02_lc_000001_V01_east_tfa_lc.tbl
    http://exoplanetarchive.ipac.caltech.edu:80/data/ETSS//KELT2/005/055/28/KELT_N02_lc_007676_V01_west_raw_lc.tbl
    ...

__Execute Bulk Download__

    niklas@lx1 ~/repos/dtools
    $ nodepy3 nasa/exoplanetarchive bulk-download KELT_N*_wget.bat \
        --to ~/Desktop/KELT
    [INFO - 2017-07-04 15:33:57,912]: Downloading "KELT_N02_lc_000001_V01_east_raw_lc.tbl" ...
    [INFO - 2017-07-04 15:34:00,467]: Downloading "KELT_N02_lc_000001_V01_east_tfa_lc.tbl" ...
    [INFO - 2017-07-04 15:34:02,585]: Downloading "KELT_N02_lc_007676_V01_west_raw_lc.tbl" ...
    ...

  [0]: https://exoplanetarchive.ipac.caltech.edu/bulk_data_download/
  [1]: https://exoplanetarchive.ipac.caltech.edu/bulk_data_download/KELT_wget.tar.gz
  [IPAC Table Format]: http://irsa.ipac.caltech.edu/applications/DDGEN/Doc/ipac_tbl.html
  [astropy]: http://docs.astropy.org
