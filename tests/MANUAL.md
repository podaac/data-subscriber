# Manual test cases (to automate)

## Subscriber


### Test 1
use to test:
* download to `this` directory.
* download using only 'enddate'
* download to a year/day-of-year directory
```
python subscriber/podaac_data_subscriber.py -c ECCO_L4_ATM_STATE_05DEG_DAILY_V4R4 -ed 1992-01-03T00:00:00Z -d ./  -dydoy
```

results in:
```
tree ./1992/
./1992/
├── 001
│   └── ATM_SURFACE_TEMP_HUM_WIND_PRES_day_mean_1992-01-01_ECCO_V4r4_latlon_0p50deg.nc
├── 002
│   └── ATM_SURFACE_TEMP_HUM_WIND_PRES_day_mean_1992-01-02_ECCO_V4r4_latlon_0p50deg.nc
└── 003
    └── ATM_SURFACE_TEMP_HUM_WIND_PRES_day_mean_1992-01-03_ECCO_V4r4_latlon_0p50deg.nc
```


### Test 2
use to test:
* cycle based directory layouts
* Bounding box limiting search results

```
python subscriber/podaac_data_subscriber.py -c JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F -d ./JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F  -dc -sd 2022-01-01T00:00:00Z -ed 2022-01-02T00:00:00Z -b="-20,-20,20,20"
```
should result in
```
tree JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F/
JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F/
└── c0042
   ├── S6A_P4_2__LR_STD__NR_042_071_20211231T232728_20220101T012144_F04.nc
   ├── S6A_P4_2__LR_STD__NR_042_082_20220101T090557_20220101T104242_F04.nc
   ├── S6A_P4_2__LR_STD__NR_042_083_20220101T104242_20220101T123506_F04.nc
   ├── S6A_P4_2__LR_STD__NR_042_095_20220101T215702_20220101T234905_F04.nc
   └── S6A_P4_2__LR_STD__NR_042_097_20220101T234905_20220102T014431_F04.nc

1 directory, 5 files

```

### Test 3
use to test:
* offset Usage
* start/end date is working
* update file working

```
rm MUR25-JPL-L4-GLOB-v04.2/.update
python subscriber/podaac_data_subscriber.py -c MUR25-JPL-L4-GLOB-v04.2 -d ./MUR25-JPL-L4-GLOB-v04.2  -sd 2020-01-01T00:00:00Z -ed 2020-01-02T00:00:00Z -dymd --offset 4
```
should yield:

```
MUR25-JPL-L4-GLOB-v04.2/.update
MUR25-JPL-L4-GLOB-v04.2/2020/01/02/20200102090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc
MUR25-JPL-L4-GLOB-v04.2/2020/01/01/20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc
```
run AGAIN to ensure no new files are downloaded

## Downloader

### Test 1

```
rm MUR25-JPL-L4-GLOB-v04.2
python subscriber/podaac_data_downloader.py -c MUR25-JPL-L4-GLOB-v04.2 -d ./MUR25-JPL-L4-GLOB-v04.2  -sd 2020-01-01T00:00:00Z -ed 2020-01-02T00:00:00Z -dymd --offset 4
```
should yield:

```
tree MUR25-JPL-L4-GLOB-v04.2/
MUR25-JPL-L4-GLOB-v04.2/
└── 2020
    └── 01
        ├── 01
        │   └── 20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc
        └── 02
            └── 20200102090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc

4 directories, 2 files
```


run AGAIN to ensure files are re-downloaded

```
rm MUR25-JPL-L4-GLOB-v04.2/2020/01/01/20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc
rm MUR25-JPL-L4-GLOB-v04.2/2020/01/02/20200102090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc
python subscriber/podaac_data_downloader.py -c MUR25-JPL-L4-GLOB-v04.2 -d ./MUR25-JPL-L4-GLOB-v04.2  -sd 2020-01-01T00:00:00Z -ed 2020-01-02T00:00:00Z -dymd --offset 4
```
should result in

```
tree MUR25-JPL-L4-GLOB-v04.2/
MUR25-JPL-L4-GLOB-v04.2/
└── 2020
    └── 01
        ├── 01
        │   └── 20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc
        └── 02
            └── 20200102090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc

4 directories, 2 files
```

### Test 2
use to test:
* cycle based directory layouts
* Bounding box limiting search results

```
python subscriber/podaac_data_downloader.py -c JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F -d ./JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F  -dc -sd 2022-01-01T00:00:00Z -ed 2022-01-02T00:00:00Z -b="-20,-20,20,20"
```
should result in
```
tree JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F/
JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F/
└── c0042
   ├── S6A_P4_2__LR_STD__NR_042_071_20211231T232728_20220101T012144_F04.nc
   ├── S6A_P4_2__LR_STD__NR_042_082_20220101T090557_20220101T104242_F04.nc
   ├── S6A_P4_2__LR_STD__NR_042_083_20220101T104242_20220101T123506_F04.nc
   ├── S6A_P4_2__LR_STD__NR_042_095_20220101T215702_20220101T234905_F04.nc
   └── S6A_P4_2__LR_STD__NR_042_097_20220101T234905_20220102T014431_F04.nc

1 directory, 5 files

```
