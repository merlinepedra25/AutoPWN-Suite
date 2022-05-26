#!/usr/bin/env python3
from argparse import ArgumentParser
from socket import socket, AF_INET, SOCK_DGRAM
from os import getuid
from logging import exception
from modules.color import print_colored, colors, bcolors
from modules.banners import print_banner
from modules.searchvuln import SearchSploits
from modules.scanner import TestArp, TestPing, AnalyseScanResults, PortScan, DiscoverHosts
from modules.outfile import InitializeOutput, output

__author__ = 'GamehunterKaan'

#parse command line arguments
argparser = ArgumentParser(description="AutoPWN Suite")
argparser.add_argument("-o", "--output", help="Output file name. (Default : autopwn.log)", default="autopwn.log")
argparser.add_argument("-t", "--target", help="Target range to scan. (192.168.0.1 or 192.168.0.0/24)")
argparser.add_argument("-st", "--scantype", help="Scan type. (Ping or ARP)", default="arp")
argparser.add_argument("-s", "--speed", help="Scan speed. (0-5)", default=3)
argparser.add_argument("-y", "--yesplease", help="Don't ask for anything. (Full automatic mode)",action="store_true")
args = argparser.parse_args()

outputfile = args.output
InitializeOutput(context=args.output)
DontAskForConfirmation = args.yesplease

def DetectPrivateIPAdress():
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

def DetectNetworkRange(ip):
    #split the IP address into 4 pieces and replace last part with 0/24
    return str(ip.split('.')[0]) + '.' + str(ip.split('.')[1]) + '.' + ip.split('.')[2] + '.0/24'

#use the 2 functions above if user doesn't specify an IP address and enabled automatic scan
if args.target:
    targetarg = args.target
else:
    if DontAskForConfirmation:
        PrivateIPAdress = DetectPrivateIPAdress()
        targetarg = DetectNetworkRange(PrivateIPAdress)
    else:
        print_colored("Please specify a target.", colors.cyan)
        targetarg = input()

scantype = args.scantype
scanspeed = int(args.speed)

#print a beautiful banner
print_banner()

output.OutputBanner(targetarg, scantype, scanspeed)

def is_root():
    if getuid() == 0:
        return True #return True if the user is root
    else:
        return False

if is_root() == False:
    print_colored("It's recommended to run this script as root since it's more silent and accurate.", colors.red)

try:
    args.speed = int(args.speed)
except ValueError:
    print_colored("Speed must be a number!", colors.red)
    args.speed = 3
    print_colored("Using default speed : %d" % args.speed, colors.cyan) #Use default speed if user specified invalid speed value type

if not args.speed <= 5 or not args.speed >= 0:
    print_colored("Invalid speed specified : %d" % args.speed, colors.red)
    args.speed = 3
    print_colored("Using default speed : %d" % args.speed, colors.cyan) #Use default speed if user specified invalid speed value

#ask the user if they want to scan ports
def UserWantsPortScan():
    if DontAskForConfirmation:
        return True
    else:
        print_colored("\nWould you like to run a port scan on these hosts? (Y/N)", colors.blue)
        while True:
            wannaportscan = input().lower()
            if wannaportscan == 'y' or wannaportscan == 'yes':
                return True
                break
            elif wannaportscan == 'n' or wannaportscan == 'no':
                output.WriteToFile("User refused to run a port scan on these hosts.")
                return False
            else:
                print("Please say Y or N!")

#ask the user if they want to do a vulnerability check
def UserWantsVulnerabilityDetection():
    if DontAskForConfirmation:
        return True
    else:
        print_colored("\nWould you like to do a version based vulnerability detection? (Y/N)", colors.blue)
        while True:
            wannaportscan = input().lower()
            if wannaportscan == 'y' or wannaportscan == 'yes':
                return True
                break
            elif wannaportscan == 'n' or wannaportscan == 'no':
                output.WriteToFile("User refused to do a version based vulnerability detection.")
                return False
            else:
                print("Please say Y or N!")

#post scan stuff
def FurtherEnumuration(hosts):
    for host in hosts:
        print("\t\t" + host)
        output.WriteToFile("\t\t" + host)
    if UserWantsPortScan():
        for host in hosts:
            output.WriteToFile("\n" + "-" * 50)
            PortScanResults = PortScan(host, scanspeed)
            PortArray = AnalyseScanResults(PortScanResults,host)
            if len(PortArray) > 0:
                if UserWantsVulnerabilityDetection():
                    SearchSploits(PortArray)
            else:
                print("Skipping vulnerability detection for " + str(host))
                output.WriteToFile("Skipped vulnerability detection for " + str(host))
            output.WriteToFile("\n" + "-" * 50)

#main function
def main():
    OnlineHosts = DiscoverHosts(targetarg, scantype, scanspeed)
    FurtherEnumuration(OnlineHosts)

#only run the script if its not imported as a module (directly interpreted with python3)
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_colored("Ctrl+C pressed. Exiting.", colors.red)
        output.WriteToFile("QUIT")