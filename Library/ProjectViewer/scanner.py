import usb

backend = usb.backend.libusb1.get_backend(find_library=lambda x: "C:\libusb-1.0.20\MS64\dll\libusb-1.0.dll")
dev = usb.core.find(backend=backend, find_all=True)