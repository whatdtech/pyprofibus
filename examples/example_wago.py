#!/usr/bin/env python3
#
# Simple pyprofibus example
#
# This example initializes an WAGO 750-343 slave, reads input
# data and writes the data back to the module.
#
# The hardware configuration is as follows:
#
#   v--------------v----------v----------v----------v----------v----------v-------------v
#   |     750-343  | 750-610  | 750-430  | 750-430  | 750-530  | 750-530  | 750-600     |
#   |              |          |  DC24V   |  DC24V   |DC24V/0.5A|DC24V/0.5A| TERMINATING |
#   |              | POWER    | 8 CHAN   | 8 CHAN   | 8 CHAN   | 8 CHAN   |   MODULE    |
#   |              | SUPPLY   | INPUTS   | INPUTS   | OUTPUTS  | OUTPUTS  |             |
#   |   WAGO       | MODULE   |3ms FILTER|3ms FILTER|          |          |             |
#   | PROFIBUS     |          |          |          |          |          |             |
#   | INTERFACE    |  DC24V   |  DC24V   |  DC24V   |  DC24V   |  DC24V   |             |
#   |  MODULE      |          |          |          |          |          |             |
#   |              |          |          |          |          |          |             |
#   |              |          |          |          |          |          |             |
#   |              |          |          |          |          |          |             |
#   ^--------------^----------^----------^----------^----------^----------^-------------^
#
#

import sys
sys.path.insert(0, "..")
import pyprofibus
import time

def main(confdir=".", watchdog=None):

	master = None
	global byteArray
	try:
		# Parse the config file.
		config = pyprofibus.PbConf.fromFile(confdir + "/examples_wago.conf")

		# Create a DP master.
		master = config.makeDPM()

		# Create the slave descriptions.
		outData = {}
		for slaveConf in config.slaveConfs:
			slaveDesc = slaveConf.makeDpSlaveDesc()

			# Set User_Prm_Data
			dp1PrmMask = bytearray((pyprofibus.dp.DpTelegram_SetPrm_Req.DPV1PRM0_FAILSAFE,
						pyprofibus.dp.DpTelegram_SetPrm_Req.DPV1PRM1_REDCFG,
						0x00))
			dp1PrmSet  = bytearray((pyprofibus.dp.DpTelegram_SetPrm_Req.DPV1PRM0_FAILSAFE,
						pyprofibus.dp.DpTelegram_SetPrm_Req.DPV1PRM1_REDCFG,
						0x00))
			slaveDesc.setUserPrmData(slaveConf.gsd.getUserPrmData(dp1PrmMask=dp1PrmMask,
									      dp1PrmSet=dp1PrmSet))

			# Register the ET-200S slave at the DPM
			master.addSlave(slaveDesc)

			# Set initial output data.
			outData[slaveDesc.name] = bytearray((0x00,0x00))
		# Initialize the DPM
		master.initialize()

		# Cyclically run Data_Exchange.
		while True:
			# Write the output data.
			for slaveDesc in master.getSlaveList():
				slaveDesc.setMasterOutData(outData[slaveDesc.name])

			# Run slave state machines.
			handledSlaveDesc = master.run()
			# Get the in-data (receive)
			if handledSlaveDesc:
				inData = handledSlaveDesc.getMasterInData()
				if inData is not None:
                                        #inputs = inData
					# In our example the output data shall be a mirror of the input.
                                        outData[handledSlaveDesc.name][0] = int(inData[0])
                                        outData[handledSlaveDesc.name][1] = int(inData[1])
			# Feed the system watchdog, if it is available.
			if watchdog is not None:
				watchdog()
			time.sleep(0.01) # Added this pause so the program does not run full speed (it loads a core to 100%)

	except pyprofibus.ProfibusError as e:
		print("Terminating: %s" % str(e))
		return 1
	finally:
		if master:
			master.destroy()
	return 0

if __name__ == "__main__":
	sys.exit(main())
