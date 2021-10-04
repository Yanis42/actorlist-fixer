import xml.etree.ElementTree as ET
import xml.dom.minidom as MD
import lists


tree = ET.parse('./ActorNames.xml')
root = tree.getroot()

actorID = lists.actorID
objectID = lists.objectID

# --- Process the original file's elements --- #

# Process Actor IDs
i = j = 0
tmp2 = []
for i in range(len(actorID)):
	if i < 16:
		idNumber = '000'
	elif i > 15 and i < 256:
		idNumber = '00'
	else:
		idNumber = '0'
	idNumber += f'{i:X}'

	for actorNode in root:
		if actorNode.get('ActorID') == idNumber:
			actorNode.set('ID', actorID.get(idNumber))
			actorNode.attrib.pop('ActorID', None)

# Process Object IDs
i = 0
for i in range(len(objectID)):
	if i < 16:
		idNumber = '000'
	elif i > 15 and i < 256:
		idNumber = '00'
	else:
		idNumber = '0'
	idNumber += f'{i:X}'

	for actorNode in root:
		if actorNode.get('ObjectID') == idNumber:
			actorNode.set('ObjectID', objectID.get(idNumber))

		elif actorNode.get('ObjectID') is not None:
			tmp = actorNode.get('ObjectID')
			if tmp.find(',') != -1:
				tmp2 = tmp.split(',')
				for j in range(len(tmp2)):
					if tmp2[j] == idNumber:
						tmp2[j] = objectID.get(idNumber)

				if len(tmp2) == 2: actorNode.set('ObjectID', tmp2[0] + ',' + tmp2[1])
				if len(tmp2) == 3: actorNode.set('ObjectID', tmp2[0] + ',' + tmp2[1] + ',' + tmp2[2])

# Generate the properties lists
listProp, listProp2, listPropNames, listPropTarget = [], [], [], []
i = j = 0
# f = open('propDebug.txt', 'w')
for actorNode in root:
	# Process Properties
	listProp.append(actorNode.get('Properties'))
	if i < len(listProp):
		if listProp[i] is not None:
			strProp = f"{listProp[i]}"

			if strProp.find(',') != -1:
				tmp = strProp.split(',')
				for j in range(len(tmp)):
					tmp[j] = '0x' + tmp[j]
				listProp2.append(tmp)
			else: listProp2.append('0x' + strProp)
		else:
			listProp2.append('0x0000')

	# Process PropertiesNames
	propNames = actorNode.get('PropertiesNames')
	if propNames is not None:
		if propNames.find(',') == -1:
			listPropNames.append(propNames)
		else:
			tmp = propNames.split(',')
			listPropNames.append(tmp)
	else:
		listPropNames.append("None")

	# Process PropertiesNames
	propTarget = actorNode.get('PropertiesTarget')
	if propTarget is not None:
		if propTarget.find(',') == -1:
			listPropTarget.append(propTarget)
		else:
			tmp = propTarget.split(',')
			listPropTarget.append(tmp)
	else:
		listPropTarget.append("None")

	# f.write(f"[Actor: {actorNode.get('ActorID')}]: [Properties: {listProp2[i]}] - [Names: {listPropNames[i]}] - [Target: {listPropTarget[i]}]\n")
	i += 1
# f.close()

# --- Change the structure of the file --- #

i = j = 0
for actorNode in root:
	# Remove Properties
	actorNode.attrib.pop('Properties', None)
	actorNode.attrib.pop('PropertiesNames', None)
	actorNode.attrib.pop('PropertiesTarget', None)
	
	for elem in actorNode.iter('Notes'):
		elem.text = ""

	# Generate the sub-elements
	propName = listPropNames[i]
	propTarget = listPropTarget[i]
	if propName is not 'None':
		# If the current element is not a list
		if isinstance(propName, list) is False:
			# Generate the sub-elements SwitchFlag, ChestFlag and by default, Property
			if propName == 'Switch Flag':
				switchFlag = { 'Flag': listProp2[i] }
				ET.SubElement(actorNode, 'SwitchFlag', switchFlag)
				for elem in actorNode.iter('SwitchFlag'):
					if propTarget is not 'None':
						elem.set('Target', propTarget)
			
			elif propName.startswith('Switch Flag '):
				switchFlag = { 'Flag': listProp2[i] }
				ET.SubElement(actorNode, 'SwitchFlag', switchFlag)
				for elem in actorNode.iter('SwitchFlag'):
					if elem.get('Flag') == listProp2[i]:
						elem.text = propName

					if propTarget is not 'None':
						elem.set('Target', propTarget)

			elif propName == 'Chest Flag':
				chestFlag = { 'Flag': listProp2[i] }
				ET.SubElement(actorNode, 'ChestFlag', chestFlag)
				for elem in actorNode.iter('ChestFlag'):
					if propTarget is not 'None':
						elem.set('Target', propTarget)

			else:
				propertyID = { 'ID': listProp2[i] }
				ET.SubElement(actorNode, 'Property', propertyID)

				for elem in actorNode.iter('Property'):
					elem.set('Name', propName)
					if propTarget is not 'None':
						elem.set('Target', propTarget)
		
		# If the current element is a list
		elif isinstance(propName, list):
			# Generate the same sub-elements but now we're dealing with lists containing strings instead of strings
			for j in range(len(propName)):
				if propName[j] == 'Switch Flag':
					switchFlag = { 'Flag': listProp2[i][j] }
					ET.SubElement(actorNode, 'SwitchFlag', switchFlag)
					for elem in actorNode.iter('SwitchFlag'):
						if propTarget is not 'None':
							elem.set('Target', propTarget[j])

				elif propName[j].startswith('Switch Flag '):
					switchFlag = { 'Flag': listProp2[i][j] }
					ET.SubElement(actorNode, 'SwitchFlag', switchFlag)
					for elem in actorNode.iter('SwitchFlag'):
						if elem.get('Flag') == listProp2[i][j]:
							elem.text = propName[j]

						if propTarget is not 'None':
							elem.set('Target', propTarget[j])

				elif propName[j] == 'Chest Flag':
					chestFlag = { 'Flag': listProp2[i][j] }
					ET.SubElement(actorNode, 'ChestFlag', chestFlag)
					for elem in actorNode.iter('ChestFlag'):
						if propTarget is not 'None':
							elem.set('Target', propTarget[j])

				else:
					propertyID = { 'ID': listProp2[i][j] }
					ET.SubElement(actorNode, 'Property', propertyID)

					for elem in actorNode.iter('Property'):
						elem.set('Name', propName[j])
						if propTarget is not 'None':
							elem.set('Target', propTarget[j])
	
	i += 1

# --- Write the new file ---

# Formatting
xmlStr = MD.parseString(ET.tostring(root)).toprettyxml(indent="  ", encoding='UTF-8')
xmlStr = b'\n'.join([s for s in xmlStr.splitlines() if s.strip()])

# Writing
with open('./ActorList.xml', 'bw') as f:
	f.write(xmlStr)
