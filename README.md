# flask-wol-api
This is a REST API built with Flask to send magic packets for WOL.  
  
Feel free to download the code, adjust it and host it yourself via pythonanywhere or any hosting service you wish.  

## How it works

The magic packets are sent by POSTing to /wol/wake with the correct MAC-Address, IP-Address or hostname of the network the PC you want to wake is in, the Port and if you want the secureOn password. You can either host it in you own network or, as mentioned, with a hosting service, which makes WOL over the internet possible, if you have the corresponding port forwarding set up in you desired network.  
You can also just provide a secureOn password. The Api will then check if it finds that password in its database. If that is the case, it will automatically send a wol packet to the devices data stored in the database for that secureOn password. You would have to manually add this entry to the database.
