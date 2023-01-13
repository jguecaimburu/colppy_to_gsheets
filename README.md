# Getting Started

## Disclaimer

Do not trust this code too much. Copy whatever you need but test it first as it was implemented as a junior attempt to optimize a manual process. 

## Overview

[Colppy](https://www.colppy.com) is an accounting software for small business owners. While they provide some solutions to connect with banks and major ecommerce platforms, they lack a good interface to analyze business information.

On the other hand, Google Sheets provides entrepreneurs a good solution to analyze their data. This project intends to provide a way to take your data from Colppy API directly into Google Sheets.

As of May 2020, you can take this following data from Colppy:

- Companies
- Cost Centers
- Invoices
- Accounting movements
- Inventory
- Deposits

Colppy payload templates for this calls come preloaded.

Automatic upload to Google Sheets is only built for inventory, but it's easy to extend the solution for other API calls.

## Installation / Usage

Clone the repo:

```
$ git clone https://github.com/jguecaimburu/colppy-to-gsheets.git
```

`app_configuration.json` needs to be complete and present in the `config` folder. You can complete `app_configuration_template.json` and change the file name.

To get Colppy credentials, go to [Colppy API](https://colppy.atlassian.net) documentation website. Once Colppy credentials are set, you can start making calls to it even if Google Sheets is not yet connected. That way you can get some information, like available companies IDs, that can be pasted in `app_configuration.json` file to use it as a cache.

To get Google client credentials, please refer to the fantastic guide written in [gspread-pandas](https://github.com/aiguofer/gspread-pandas) and paste them in the configuration file. This package will be quite useful if you want to connect Pandas to Google Spreadsheets.

Please be aware, `app_configuration.json` contains your private credentials, so take care of the file in the same way you care of your private SSH key.
