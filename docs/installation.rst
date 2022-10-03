Installation
============

**In Windows**

1. Beginner Method

a. Visit PyLUSAT GitHub repository Click **Code**, and then **Download ZIP** to download the *pylusat-qgis* repository.
b. Copy ``pylusat_installer.bat``, paste it under QGIS folder in your system.
c. Right Click the copied ``pylusat_installer.bat`` to **Run as administrator**.

2. Advanced Method

a. Visit PyLUSAT GitHub repository. Copy and paste the code in pylusat_installer.bat to your terminal under the QGIS folder and run it.
b. **Specify your root folder of QGIS**: The same place as the pylusat_installer.
c. **Is the QGIS a long term release [Y/N]**: Refer to the version you installed. Type Y for long term release. N for short term release.
d. Press **Enter** key and wait for installation to complete.

**In macOS**

Use ``pip install pylusat`` in Python Command Prompt of **QGIS**.

Install PyLUSAT plugin
----------------------

1. Download **PyLUSAT plugin** from https://plugins.qgis.org/plugins/pylusatq/.
2. Find **Plugins** on the top panel in your **QGIS Desktop**, Click **Manage and install plugins**.
3. In **Install from ZIP** interface, browse and select the PyLUSAT ZIP file you download.
4. Click Install Plugin, once finished, restart QGIS.
5. Now you can find PyLUSAT tools in Processing Toolbox panel.