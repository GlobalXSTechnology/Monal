# Universal Serial Number in One2many List Views

**Module Name:** serial_number_one2many  
**Odoo Version:** 18.0  
**Category:** Tools  
**Author:** Mohsan Raza  
**Website:** [MR Wattoo](https://www.mrwattoo.com)  
**License:** LGPL-3  

## Overview

This module adds automatic serial numbers to all One2many list views in Odoo 18.  
It displays row numbers dynamically in embedded list views without any extra configuration.

**Key Features:**
- Automatically adds serial numbers (`Sr.`) to all One2many fields.
- Works for all models inheriting from `base`.
- No need to modify individual models or views.
- Pure Python implementation using `compute` fields.
- Lightweight and non-intrusive.

## Installation

1. Download or clone the module into your Odoo `addons` directory.
2. Update the app list in Odoo.
3. Install the module `Universal Serial Number in List Views`.

## Usage

Once installed, every One2many field in your models will show a `Sr.` column with serial numbers starting from 1.  
No further configuration is needed.

## License

This module is released under the [LGPL-3](https://www.gnu.org/licenses/lgpl-3.0.html) license.

## Support

For support or contributions, please visit the [GitHub repository](https://github.com/OCA/web).