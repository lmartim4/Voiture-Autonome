# How to work with this project

The best way we found to quiclky code was to connect VSCode to the raspi via ssh.

* Download and Install [VSCode](https://code.visualstudio.com/download) in your laptop.

* Make sure the Laptop and the Raspi are connected to the same network. You must already have the network set up. Refer to [Wi-FI setup](/docs//A_WIFI_SETUP.md) if not.


What we will be setting up is well documented on this [resource](https://code.visualstudio.com/docs/remote/ssh)

It consists of installing [Remote SSH Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh) to your VSCode on your laptop.



![](/docs/images/vscode_setup/install_remote_ssh.png)


**Hit F1** to open command search menu an then do the following:

![](/docs/images/vscode_setup/connect_to_host.png)


![](/docs/images/vscode_setup/configure_new_host.png)

Once you are on the config file, you should add the following structure to the file in order to register the voiture name, IP and username.

```
Host Voiture-Jaune
  HostName 172.20.10.3
  User ensta
  ForwardAgent yes
  ForwardX11Trusted yes
```

If VSCode can hit the raspi via an ssh connection request you will be prompted with the use password. The password should be "**ensta**" (without quotation marks). If it doesn't work check if both laptop and raspi are connected to the same Wi-Fi hotspot.

![](/docs/images/vscode_setup/insert_password.png)

![](/docs/images/vscode_setup/open_right_folder.png)

In the following image you should be in the main worspace development.

![](/docs/images/vscode_setup/open_code_subfolder.png)

You can trust the raspi :)

![](/docs/images/vscode_setup/trust.png)

Make sure you install [Python VSCode Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python). It will create nice shorcuts.

Try opening the terminal to check if the system is working properly:


![](/docs/images/vscode_setup/terminal.png)