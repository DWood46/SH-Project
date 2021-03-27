#include <Windows.h>
#include <iostream>
#include <sstream>
#include <vector>
#include <TlHelp32.h>
#include <tchar.h>
#include <Psapi.h>
#include <string>
#include <stdlib.h>

using namespace std;

//Note: set to multi-byte character set

/**
 Get the base address of the module from the given pID

 @param pID         Program ID
 @param module      Module to find address of
 @return            Module's base address
 */
uintptr_t getModuleBaseAddress(DWORD pID, TCHAR* module) {
    uintptr_t baseAddress = 0;
    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pID);
    if (hSnapshot != INVALID_HANDLE_VALUE) {
        MODULEENTRY32 modEntry;
        modEntry.dwSize = sizeof(modEntry);
        //Iterate through list of modules
        if (Module32First(hSnapshot, &modEntry)) {
            do {
                //If module found, return it
                if (!_tcsicmp(modEntry.szModule, module)) {
                    baseAddress = (uintptr_t)modEntry.modBaseAddr;
                    break;
                }
            } while (Module32Next(hSnapshot, &modEntry));
        }
    }
    CloseHandle(hSnapshot);
    return baseAddress;
}

/**
 Read the memory of the given address and iterate through the list of offsets provided, continually
 reading the memory of the locations provided.

 @param pHandle     Program's handle
 @param address     Initial address
 @param offsets     Vector containing the list of offsets to add to the pointers read
 @return            Final memory address
 */
uintptr_t findOffsetAddress(HANDLE pHandle, uintptr_t baseAddress, std::vector<unsigned int> offsets) {
    //current address
    uintptr_t address = baseAddress;
    //Iterate through list of offsets
    for (unsigned int i = 0; i < offsets.size(); ++i) {
        ReadProcessMemory(pHandle, (BYTE*)address, &address, sizeof(address), 0);
        address += offsets[i];
    }
    return address;
}

int main(int argc, char* argv[]) {
    DWORD pID;
    int value;
    uintptr_t baseAddress;
    HWND hGameWindow;
    HANDLE pHandle;

    string description;
    LPCSTR windowName;
    TCHAR* moduleName;
    unsigned int initialOffset;
    std::vector<unsigned int> offsets = { };

    if (argc < 4) {
        cout << "USAGE: MemoryReader.exe window_name module_name initial_offset [offset1, offset2...]" << argv[2] << std::endl;
        return 0;
    }
    else {
        windowName = argv[1];
        moduleName = argv[2];
        initialOffset = strtoul(argv[3], NULL, 0);
        if (argc > 3) {
            for (unsigned int i = 4; i < argc; ++i) {
                offsets.push_back(strtoul(argv[i], NULL, 0));
            }
        }
    }

    //Get process handle
    hGameWindow = FindWindow(NULL, windowName);
    GetWindowThreadProcessId(hGameWindow, &pID);
    pHandle = OpenProcess(PROCESS_ALL_ACCESS, NULL, pID);

    if (!pHandle) {
        cout << "ERROR: no process found" << std::endl;
        exit(EXIT_FAILURE);
    }

    //Get base address
    uintptr_t clientBase = getModuleBaseAddress(pID, _T(moduleName));
    
    //Add initial offset
    clientBase += initialOffset;

    //Obtain final address
    uintptr_t finalAddress = findOffsetAddress(pHandle, clientBase, offsets);

    //Print contents to stdout
    ReadProcessMemory(pHandle, (BYTE*)finalAddress, &value, sizeof(value), NULL);
    cout << std::dec << value << std::endl;
}