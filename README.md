[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## dtools

Dtools is a collection of scripts to for downloading and preparing large
datasets from *specific* providers. Dtools is not a generic tool for data
retrieval.

### Usage

  [Node.py]: https://nodepy.org/

There is no installation process for dtools itself. You will need Python 3
and [Node.py] to run the scripts, though, and install the dtools dependencies.

    $ pip3 install --user nodepy-runtime
    $ git clone https://github.com/NiklasRosenstein/dtools.git
    $ cd dtools
    $ nodepy-pm install

### Supporter Providers

* [ESA Gaia Archive](#esa-gaia-archive)
* [NASA Exoplanet Archive](#nasa-exoplanet-archive)

---

### ESA Gaia Archive

  [ESA_1]: http://gea.esac.esa.int/archive/
  [ESA_2]: http://sci.esa.int/
  [ESA_3]: http://sci.esa.int/gaia/

The ESA's ([European Space Agency][ESA_2]) [GAIA satellite][ESA_3] data
archive can be found [here][ESA_1]. They provide a bulk download option in
various formats. You can easily download all or specific parts from the
archive with dtools.

    $ nodepy esa/gaia -- help
    ...
    $ nodepy esa/gaia --parallel 4 --to ~/Desktop/GAIA --unpack --range2 0
    [INFO - 2017-07-05 13:21:13,576]: Downloading "GaiaSource_000-000-003.csv.gz" ...
    [INFO - 2017-07-05 13:21:13,577]: Downloading "GaiaSource_000-000-001.csv.gz" ...
    [INFO - 2017-07-05 13:21:13,585]: Downloading "GaiaSource_000-000-000.csv.gz" ...
    [INFO - 2017-07-05 13:21:13,589]: Downloading "GaiaSource_000-000-002.csv.gz" ...
    [INFO - 2017-07-05 13:21:38,830]: Unpacking "GaiaSource_000-000-001.csv.gz" ...
    [INFO - 2017-07-05 13:21:39,713]: Downloading "GaiaSource_000-000-004.csv.gz" ...
    ...

**Note:** The full GAIA dataset (as of 2017/07/05) features 5231 table parts
and its full uncompressed size amounts to about 510GB! The TGAS table consists
of 16 parts and amounts to about 1.5GB (uncompressed).

---

### NASA Exoplanet Archive

  [NASA_1]: https://exoplanetarchive.ipac.caltech.edu/bulk_data_download/
  [NASA_2]: https://exoplanetarchive.ipac.caltech.edu/bulk_data_download/KELT_wget.tar.gz
  [NASA_3]: https://exoplanetarchive.ipac.caltech.edu/docs/KELT.html
  [IPAC Table Format]: http://irsa.ipac.caltech.edu/applications/DDGEN/Doc/ipac_tbl.html
  [astropy]: http://docs.astropy.org

The [NASA Exoplanet Archive][NASA_1] offers bulk data downloads which actually
only provides scripts for the bulk-download that in turn use `wget`. If you
don't have `wget` installed or you simply want to extract all URLs instead of
downloading them, this is where dtools comes in handy.

For example, you can download the [KELT][NASA_3] timeseries data from [here][NASA_2]
(in [IPAC Table Format] which can be read by [astropy]), extract the `.bat` files
and pass them to the script to extract the download URLs, or download them
immediately.

__Extract URLs__

    $ nodepy nasa/exoplanetarchive extract-urls ~/Downloads/KELT_N*_wget.bat
    http://exoplanetarchive.ipac.caltech.edu:80/data/ETSS//KELT2/005/055/28/KELT_N02_lc_000001_V01_east_raw_lc.tbl
    http://exoplanetarchive.ipac.caltech.edu:80/data/ETSS//KELT2/005/055/73/KELT_N02_lc_000001_V01_east_tfa_lc.tbl
    http://exoplanetarchive.ipac.caltech.edu:80/data/ETSS//KELT2/005/055/28/KELT_N02_lc_007676_V01_west_raw_lc.tbl
    ...

__Execute Bulk Download__

    $ nodepy nasa/exoplanetarchive bulk-download KELT_N*_wget.bat \
        --to ~/Desktop/KELT --parallel 4
    [INFO - 2017-07-04 16:12:23,556]: Spawning 4 threads ...
    [INFO - 2017-07-04 16:12:23,557]: Thread 0 started.
    [INFO - 2017-07-04 16:12:23,557]: Thread 1 started.
    [INFO - 2017-07-04 16:12:23,557]: Thread 2 started.
    [INFO - 2017-07-04 16:12:23,557]: Thread 3 started.
    [INFO - 2017-07-04 16:12:23,559]: Downloading "KELT_N04_lc_000001_V01_east_raw_lc.tbl" ...
    [INFO - 2017-07-04 16:12:23,559]: Downloading "KELT_N04_lc_000001_V01_east_tfa_lc.tbl" ...
    [INFO - 2017-07-04 16:12:23,561]: Downloading "KELT_N04_lc_020344_V01_west_raw_lc.tbl" ...
    ...

**Tip:** You can use the [KELT][NASA_3] website to go to the Timeseries or Praesepe
database search pages, conduct an empty search, wait for the results and then
download the whole database in various formats (including IPAC .tbl and CSV).
