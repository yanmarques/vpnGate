# vpnGate
Free auto-maintain VPN service to surf the web.

The main reason I stopped developing this is because I lost some work which was offline and I got really pissed off, and also because I had to focus on another personal stuff.

So I am decided to finish this work as a proof of concept. I have started to document things (which I had not, very very bad). But if you got interested you can check the [tree-token](https://github.com/yanmarques/vpnGate/tree/tree-token) branch which is the latest one, notice that the file `lib/node.py` is missing because of wrong code base management, I am trying to get it better though. But you can check the tests  and the code at `blueprints/{blocks.py,landing.py}` to get an idea of what it does under the hood.

# Nice idea, but mainly impratical
## How it began?
I started developing this tool (I call this a tool based on this not being a simple program you run in your computer) because I was really concerned about my digital privacy and security. Firstly, as always, after a lot of research about the topic I was even more lost than before it. Anyways, when one paranoid person (like me) starts to wonder about too much thing that could happen, the focus is easily lost and the main reason is forgotten. This tool is the consequence of this process, besides I learned a lot ;)

## Things I learned
A lot. Actually more than I can put in words, but I will try to summarize some. 
I was always interested about security, dev-ops and that kind of stuff, but learn these by yourself was hard in the beggining. The time is gone and now after a few years of experience it kinda takes an automatically flow in my mind, this is not something you can learn in college, online courses, wathever...
Moving on, in the researchs I've made, I got to the conclusion that one can not (easily) have privacy AND security together, at least stronger ones. Generally, it is a choice one has to make.

### What is VPN
Firstly, VPN stands for Virtual Private Network, and you can get an idea that it connects remote networks. The VPNs use got a bloom when privacy/security topics became popular and people ran fast to get one. But hang on, we are hackers, let's hack it first. Initially VPNs were used by Corporations who wanted to share their resources (like database, web server, etc...) with employees all around the world, that means a home office employee could work from home and access everything he/she needed, but safely. The keyword here is __safely__. The Corporation could expose their resources to the whole internet and enforce authentication for each service, so only authorized employees could access them with theirs credentials. The problem is that the whole internet is too much, anyone out there could impersonate the service, bruteforce it, or even abuse some vulnerability of the given service. Without even saying that is a huge work to keep all services with authentication, fully updated with security patches and so on, this is overwhelming. 

The solution found was to use a VPN. Different from username/password common authentication mechanisms, the VPN provides stronger credentials, with very hard to crack passwords (technically called keys). Now the Corporation will only need to worry about one server, the VPN one, which contains the secrets. Under the hoods, the VPN software will create a virtual private network on the client (the employee) and one on the server, it is virtual because it is not phisically present and has to be created in the runtime and private because the network address should be one of the private network addresses assigned by IANA, and so not publically accessable. And these two private networks, the client and server ones, are connected by a virtual cable provided by the VPN software. The VPN softwares implementation differs from each other, but all them follow the same principles.

To surf the web using a VPN, the way it is done is different from the previous use case. In the previous use case, the employees would only access some devices with the VPN, but the internet/web does not go through the VPN. Why this? We need to remember the principles, connect two remote networks. The employees would, for example, access the Corporation `10.10.10.0/24` physical network. This means that in the routing table, would exist a rule that the network `10.10.10.0/24` will be accessed through the VPN virtual interface, which would get an private IP address of the employee local virtual network.

This helps ilustrating the employee connecting to the private physical network through the VPN.

     ________________________        Virtual Cable        __________________________________
    | Private Net - Employee | <-----------------------> | Private Net - Corporation Server |
     ------------------------                             ----------------------------------
                                                                          /|\
                                                                           | 
                                                                           |
                                                                          \|/
                                                            ______________________________
                                                           | 10.10.10.0/24 - Physical Net |
                                                            ______________________________
                                                                      
And when you are using the VPN to surf the web, or access (almost) the entire internet, one need to understand what is `the internet` for the computer. When one is learning about machine network addressing, routing and that stuff we eventually look something called route of last resort or just default route, this is a routing rule that instruct the kernel of the current operating system that, when any other route matches the given packet, send this one to the default route and beg for it to get a response. This is basically the internet for the computers, everything that is not found anywhere else. The address for this rule is the famous `0.0.0.0/0`, which the kernel translates to everything. And that is exactly what VPNs which lets you browse the internet do, they connects the client with all networks in the server (exception of localhost and some other user defined networks). Taking the same flow explained earlier, in the routing table would exist a rule to the default route (the mysterious internet) accessed through the VPN server.

One more illustration about the VPN to surf the web.

      ____________________         Virtual Cable        ______________________
     | Private Net - User | <------------------------> | Private Net - Server |
      --------------------                              ----------------------
                                                                 /|\
                                                                  |
                                                                  |
                                                                 \|/
                                                        __________________________
                                                       | 0.0.0.0/0 - Physical Net |
                                                        __________________________

### What are VPNs benefits
This tool would provide VPN services. I will talk a little about the consequence of using VPNs, not the cause of these consequences. The sources I used to build this are spreaded into the internet, take a deep breadth and look for it. 

**What benefits do people get from VPNs?**

This applies to every VPN service in general, not just this one specifically. But a VPN will (sometimes) protect you againts:
  - local adversaries from untrusted network. Eg.: coffee's, airport's, etc... Wifi
  - IP based block. Eg.: your IP get banned from some service, when you use a VPN your IP is not showed to the mentioned service, so you are not blocked (unless your VPN's IP is also not blocked, right?!)
  
It concludes that you are as private and secure as you were without a VPN.
  
**The target people would be:**
  - poor ones, which do not have enough money to pay for a payed VPN service
  - entusiasts, which just want to test a VPN service
  - anyone else which do not care about low-latency limited-bandwidth VPN service
  
### So, why VPNs?
I guess the mainly reason is that already exists a lot of excellent solutions for free out there, like Tor, I2P, Freenet, Zeronet, etc...   
The only one which allows you to browse the internet is Tor, and it is the recommended method to do it privately. Altought there are basically two things that can be considered a con (it is like that for good reasons):
  - high-latency, you have increased random hops (generally 3) to your connection
  - exit traffic is usually blocked by common services because of bad reputation (cyber attacks, bruteforcing). There is misconception that Tor is mainly blocked, but few services activetaly blocks Tor, it is blocked by previously reasons.

So, one should surf the web with Tor, for privacy purposes. But if privacy is not a concern, I do not see the point to use it, actually you can get more exposed than you wanted. Here is where the VPN comes through, but if you are with me, it serves for very few purposes, so as any other software, it must be used carefully.

# How it works
After reading above topics about the _why to_ we get to the _how to_. As stated in this project description, it covers a free VPN service able to maintain itself. Now let's dig in about how I get to implement this, actually would get because I do not finished it, but the idea was already built. 

## Free? Auto maintain?
I agree with everything takes a cost, and to keep these service free, it cost too. The mainly costs would be from the VPN server itself, because would need a VPS running the VPN software and also a public IP. The other big cost would be the web server where people would access in order to get the credentials to the VPN. I as maintainer would maintain the VPN server on with donations and my own resources. The auto maintain part is about the web server, where would be developed a way to people around the world to help me and help others to access the web server. 

These implementation is where the magic begins, I would say. The next topics will be presented in detail how all this would be possible. But some introduction is advised. In the time I started to write this tool I was learning to play with blockchains, and what it is used for and how it works. So spoiler, all the implementation details covers using blockchains to democratise and distribute data. Let's talk a little about blockchains (one should look elsewhere for more details).

**What are blockchain?**

A data structure which holds data with a signature of this data and a value that proves you can create the assigned data. This value is usually called `proof of work` (POW), and generally it is a number very hard to find, computationally speaking, but easily to verify it's correctness. It means that every time you want to submit some `block` of data, one have to prove that spent some time looking for a proof of work. And how does this tool benefits from this? Well, the tool would use the very basic concept of proof of work, where each new user who wanted access to the VPN service, would have to spent some time calcultating the proof of work. This is not the perfect solution, based that powerfull computers would find the POW faster than slower ones.

The blockchain alone is just a piece of static democratized data. It needs to be accessed externally from other parties to exchange information. That part is aborded the next topic.

### Blockchain API
The machine needs to gather information from other machines, and send its own information to other machines. But what machines to exchange information to? When to send information to other machines? Should we trust information from other machines? 

Well these are hard questions to answer, and generally the main ones.

### Web Server
Machines running the web server, would also participate in a blockchain specifically for user's email address, which the VPN server also participates.

These machines would be responsable of:
  - exposing the web page with content to the user calculate the proof of work in their machines (using javascript) 
  - verifying users proof of work and appending user email to the blockchain wheter it not exists already 

