# SH-Project
## Note

The project uses two main components written in different languages, Python and C++. The application is run from the **/controller_application/** directory but requires compiled executables from the **/memory_reader_application/** directory. These have been provided already, but details on compiling these files is at the bottom.

## Usage

**You must be using Windows**

1. Install the latest [vc_redist.x64.exe](https://support.microsoft.com/en-gb/help/2977003/the-latest-supported-visual-c-downloads) for Visual Studio 2019.

2. Install [OBS Studio](https://obsproject.com/). Additionally, install the [obs-websocket plugin](https://github.com/Palakis/obs-websocket/releases).

3. If the virtual environment doesn't exist, create one using the following in Python 3.7+:

```bash
pip3 install virtualenv

virtualenv venv
```

4. Run the following command in the command prompt to enter the virtual environment.

```bash
venv\Scripts\activate.bat
```

5. Install requirements inside the virtual environment (if they do not already exist).

```bash
pip3 install -r requirements.txt
```

6. Run an instance of OBS Studio, configure the plugin to use a specific port and password.

7. Edit the controller application configuration files, ensuring that it has the same port as OBS, and run the application.

```bash
python Main.py
```

## Memory Reader compiling

Pre-compiled executables for the memory reader application have been provided for ease of use, but if compiling is required, follow these steps:
1. Open the .sln file in Visual Studio.
2. Configure the project to use the multi-byte character set.
	* Project &rarr; Properties &rarr; Configuration Properties &rarr; Advanced &rarr; Change the **Character Set** parameter to **Use Multi-Byte Character Set**.
3. Build the project for both x86 and x64.
4. Rename the x86 variant to **memoryreader32.exe**, and the x64 variant to **memoryreader64.exe**.
5. Place in the '/controller_application/' directory.