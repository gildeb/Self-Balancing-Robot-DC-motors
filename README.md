# Self Balancing Robot using DC motors

The robot is based on the Raspberry Pi Pico-W. It hosts a web server and is controlled by a smartphone via a web page.

## Bill of materials

- Raspberry Pi Pico-W : https://fr.aliexpress.com/item/1005006994509535.html
- MPU6050 (IMU) : https://fr.aliexpress.com/item/1005009668682906.html
- DC motors (12V333, JGB37-520) : https://fr.aliexpress.com/item/1005005900864551.html
- motor driver (L298) + voltage regulator : https://fr.aliexpress.com/item/32392774289.html
- Li-ion batteries (3x18650) : https://fr.aliexpress.com/item/1005008601296848.html
- battery holder : https://fr.aliexpress.com/item/1005006283625827.html
- micro switch : https://fr.aliexpress.com/item/1005003938856402.html
- wheels : https://fr.aliexpress.com/item/1005004190081964.html
- 3D printed parts

## Schematic
<div align="center">
<img width="408" height="330" alt="SBR DC schematic" src="https://github.com/user-attachments/assets/9a6793d9-0dad-4ebc-8e11-71ea9fed0f0f" />
</div>

## PCB
<div align="center">
<img width="425" height="255" alt="SBR DC pcb" src="https://github.com/user-attachments/assets/232d5cd7-0d6d-4eb9-b500-8c8707bdeb39" />
</div>

## WIFI connexion

In _WifiConnect.py_, update _credentials_ dictionnary with your networks SSID and passwords (home, cell phone, ...).

```python
    credentials = { 'my_SSID':'passwword',
                  # other credentials
                  }
```

Update  _SBR.py_ with your favorite one :

```python
print('WifiConnect successfull, ip =', WifiConnect('my_SSID').ifconfig()[0])
```

On successfull connexion, the IP address of RP2040 will be displayed in the interpreter output.

In your cell phone, open a browser (Chrome, Safari, ...) and just enter that address.

## Starting

To start automatically on boot, insert :

```python
import SBR
```
in _main.py_ file.

## PID constant tuning

In _SBR.py_, choose the _PID_tuning.html_ file :

```python
html_file = '/SBR/PID_tuning.html'
```

Your phone should display :

<div align="center">
<img width="828" height="1644" alt="PID_tuning" src="https://github.com/user-attachments/assets/16bbf4a2-9843-46fd-8454-fec3b752607f" />
</div>

