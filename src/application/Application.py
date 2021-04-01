from src.application.AbstractApplication import AbstractApplication


class App(AbstractApplication):
    def __init__(self, device, package_name, name="app", version="1.0"):
        super(App, self).__init__(package_name, version)
        self.name = name
        self.device = device

    def start(self):
        self.device.execute_command("monkey -p {pkg} 1".format(pkg=self.package_name), args=[], shell=True)
        self.on_fg = True

    def kill(self):
        pass

    def stop(self):
        pass

    def performAction(self, act):
        pass