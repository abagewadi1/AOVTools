

import nuke
import math
from typing import List
from typing import Set

globalComponentSet: Set[str] = {'specular', 'sss', 'gi', 'sheen', 'transmission', 'coat', 'reflection', 'refraction', 'emission', 'diffuse'}




def autoCompSplit(readNode, layers):
    """
    Create an auto comp method, that will spilt all the AOVs from the selected lighting render and rebuild a CG Comp
        Args:
            readNode (Nuke Node) : User selected readnode from the node graph
            layers (List str) : List of render AOVs 
        Returns:
            firstPrimaryMergeNodeName (str) : Name of the first primary merge node
            globalDotNodeCount (int) : Total Number of Dot Nodes in the Node Graph
    """

    #CREATING AN EMPTY SET OF COMPONENTS AND LIGHTGROUPS
    componentSet = set()
    lightGroupSet = set()
    #backdrop = nuke.createNode('Backdrop')
    #SPLITTING THE NAMES OF THE RENDER LAYERS INTO TWO PARTS: COMPONENTS AND LIGHT GROUPS
    for layer in layers:
        if layer.split('_', 1)[0].lower() in globalComponentSet:
            componentSet.add(layer.split('_', 1)[0])
        lightName = layer.split('_', 1)[-1].lower()
        if lightName != 'default' and lightName != 'diffusefilter' and lightName != 'rgba' and lightName != 'albedo':
            lightGroupSet.add(layer.split('_', 1)[-1])
    
    #READ NODE POSITION IN THE NODE GRAPH
    readNodeXPosition = readNode.xpos()
    readNodeYPosition = readNode.ypos()
    
    #CREATING AN UNPREMULT NODE
    unpremultNode = nuke.createNode('Unpremult')
    unpremultNode.setInput(0, readNode)
    unpremultNode['channels'].setValue('all')
    unpremultNode['xpos'].setValue(readNodeXPosition+200)
    unpremultNode['ypos'].setValue(readNodeYPosition+25)
    globalDotNodeCount = len(nuke.allNodes('Dot'))
    lightGroupCount = 1
    mainDotNodeCount = 0
    
    #NESTED FOR LOOPS TO CONSTRUCT THE CG COMP
    for lightGroup in lightGroupSet:
        
        #ITERATING OVER LIGHT GROUPS
        mainDotNode = nuke.createNode('Dot')
        globalDotNodeCount += 1

        #CONDITION TO CHECK IF THIS IS THE FIRST MAIN DOT
        if mainDotNodeCount == 0:
            #CONNECTS THE MAIN DOT TO THE READ NODE
            mainDotNode.setInput(0, unpremultNode)
            mainDotNode['xpos'].setValue(readNodeXPosition+400)
            mainDotNode['ypos'].setValue(readNodeYPosition+25)
            mainDotNodeCount += 1
        else:
            #CONNECTS THE MAIN DOT TO THE LAST MAIN DOT
            lastPrimaryDotNode = nuke.toNode('Dot'+str(globalDotNodeCount-(len(componentSet)+2)))
            mainDotNode.setInput(0, lastPrimaryDotNode)
            mainDotNode['xpos'].setValue(lastPrimaryDotNode.xpos()+(len(componentSet)*250))
            mainDotNode['ypos'].setValue(lastPrimaryDotNode.ypos())
        
        secondaryDotNodeCount = 0
        componentCount = 1
        flag = 'up'
        
        for component in componentSet:
            #ITERATING OVER COMPONENTS
            secondaryDotNode = nuke.createNode('Dot')
            globalDotNodeCount += 1
 
            #CONDITION TO CHECK IF THIS IS THE FIRST SECONDARY DOT
            if secondaryDotNodeCount == 0:
                #CONNECTS THE SECONDARY DOT TO THE CORRESPONDING MAIN DOT
                secondaryDotNode.setInput(0, mainDotNode)
                secondaryDotNode['xpos'].setValue(mainDotNode.xpos())
                secondaryDotNode['ypos'].setValue(mainDotNode.ypos()+200)
                secondaryDotNodeCount += 1
            else:
                #CONNECTS THE SECONDARY DOT TO THE LAST SECONDARY DOT
                if lightGroupCount != len(lightGroupSet) and flag == 'up':
                    lastSecondaryDotNode = nuke.toNode('Dot'+str(globalDotNodeCount-1))
                else:
                    if flag == 'up':
                        lastSecondaryDotNode = nuke.toNode('Dot'+str(globalDotNodeCount-2))
                        flag = 'down'
                    else:
                        lastSecondaryDotNode = nuke.toNode('Dot'+str(globalDotNodeCount-1))
                secondaryDotNode.setInput(0, lastSecondaryDotNode)  
                secondaryDotNode['xpos'].setValue(lastSecondaryDotNode.xpos()+200)
                secondaryDotNode['ypos'].setValue(lastSecondaryDotNode.ypos())
            secondaryDotNode.setSelected(False)

            #CREATING SHUFFLE NODES
            shuffleNode = nuke.createNode('Shuffle2')
            shuffleNode.setInput(0, secondaryDotNode)
            shuffleNode['xpos'].setValue(secondaryDotNode.xpos()-25)
            shuffleNode['ypos'].setValue(secondaryDotNode.ypos()+200)
            shuffleNode['in1'].setValue(component+'_'+lightGroup)
            shuffleNode['label'].setValue(component+'_'+lightGroup)
            
            #CREATING REMOVE NODES
            removeNode = nuke.createNode('Remove')
            removeNode.setInput(0, shuffleNode)
            removeNode['operation'].setValue('keep')
            removeNode['channels'].setValue('rgb')
            removeNode['xpos'].setValue(shuffleNode.xpos())
            removeNode['ypos'].setValue(shuffleNode.ypos()+100)

            #CREATING MERGE NODES
            if componentCount == 1:

                #CHECKING IF THIS IS THE FIRST COMPONENT OF THE LIGHT GROUP
                mergeNode = nuke.createNode('Merge2')
                mergeNode['operation'].setValue('plus')
                mergeNode.setInput(1, removeNode)
                mergeNode.setSelected(False)
                mergeNode['xpos'].setValue(removeNode.xpos())
                mergeNode['ypos'].setValue(removeNode.ypos()+100)
                
                #CHECKING IF THIS IS THE LAST LIGHT GROUP OF THE SET 
                if lightGroupCount != len(lightGroupSet):
                    mergeNodePrim = nuke.createNode('Merge2')
                    mergeNodePrim['operation'].setValue('plus')
                    mergeNodePrim.setInput(1, mergeNode)
                    mergeNodePrim.setSelected(False)
                    mergeNodePrim['xpos'].setValue(mergeNode.xpos())
                    mergeNodePrim['ypos'].setValue(mergeNode.ypos()+250)
                    if lightGroupCount == 1:
                        mergeNodePrimName = mergeNodePrim.name()
                        firstPrimaryMergeNodeName = mergeNodePrimName
                    else:
                        nuke.toNode(mergeNodePrimName).setInput(0, mergeNodePrim)
                        mergeNodePrimName = mergeNodePrim.name()
                else:
                    dotNodePrim = nuke.createNode('Dot')
                    dotNodePrim.setInput(0, mergeNode)
                    dotNodePrim.setSelected(False)
                    dotNodePrim['xpos'].setValue(mergeNode.xpos()+25)
                    dotNodePrim['ypos'].setValue(mergeNode.ypos()+250)
                    nuke.toNode(mergeNodePrimName).setInput(0, dotNodePrim)
                    globalDotNodeCount += 1

            elif componentCount == len(componentSet):
                
                #CHECKING IF THIS IS THE LAST COMPONENT OF THE LIGHT GROUP
                dotNode = nuke.createNode('Dot')
                dotNode.setInput(0, removeNode)
                dotNode.setSelected(False)
                dotNode['xpos'].setValue(removeNode.xpos()+25)
                dotNode['ypos'].setValue(removeNode.ypos()+100)
                globalDotNodeCount += 1
                nuke.toNode(lastMergeNodeName).setInput(0, dotNode)

            else:
                mergeNode = nuke.createNode('Merge2')
                mergeNode['operation'].setValue('plus')
                mergeNode.setInput(1, removeNode)
                mergeNode.setSelected(False)
                mergeNode['xpos'].setValue(removeNode.xpos())
                mergeNode['ypos'].setValue(removeNode.ypos()+100)
                nuke.toNode(lastMergeNodeName).setInput(0, mergeNode)
                
            lastMergeNodeName = mergeNode.name()
            componentCount += 1
        lightGroupCount += 1
    
    return firstPrimaryMergeNodeName, globalDotNodeCount
    
    
def createCopyPremultNodes(readNode, mergeNodeName, globalDotNodeCount):

    #FETCHING THE PRIMARY MERGE NODE
    mergeNodePrim = nuke.toNode(mergeNodeName)
    
    #CREATING A COPY NODE, CORESSPONDING DOT NODE AND A PREMULT NODE
    copyNode = nuke.createNode('Copy')
    copyNode.setInput(0, mergeNodePrim)
    extraDotNode = nuke.createNode('Dot')
    extraDotNode.setInput(0, readNode)
    globalDotNodeCount += 1
    copyNode.setInput(1, extraDotNode)
    copyNode['xpos'].setValue(mergeNodePrim.xpos())
    copyNode['ypos'].setValue(mergeNodePrim.ypos()+400)
    extraDotNode['xpos'].setValue(copyNode.xpos()-300)
    extraDotNode['ypos'].setValue(copyNode.ypos())
    extraDotNode.setSelected(False)
    premultNode = nuke.createNode('Premult')
    premultNode.setInput(0, copyNode)
    premultNode['xpos'].setValue(copyNode.xpos())
    premultNode['ypos'].setValue(copyNode.ypos()+100)

def aovBreakout(readNode, layers):
    """
    Breakout all the AOVs from the selected render and attach Text nodes to it
        Args:
            readNode (Nuke Node) : User selected readnode from the node graph
            layers (List str) : List of render AOVs
        Returns:
            textNodes (Nuke Node List) : All the Text nodes in the node graph
    """

    #ITERATING A LOOP OVER ALL THE LAYERS/AOVs
    for layer in layers:

        #CREATING SHUFFLE NODES, CONNECTING THEM TO THE READ NODE AND SELECTING ONE AOV AT A TIME
        shuffleNode = nuke.createNode('Shuffle2')
        shuffleNode.setInput(0, readNode)
        shuffleNode['in1'].setValue(layer)
        shuffleNode['label'].setValue(layer)

        #CREATING TEXT NODES WITH AOV NAMES IN IT AND CONNECTING THEM TO THEIR CORRESPONDING SHUFFLE NODES
        textNode = nuke.createNode('Text2')
        textNode['message'].setValue(layer)
        textNode['enable_background'].setValue(True)
        textNode['background_opacity'].setValue(0.98)

    #COLLECTING ALL THE TEXT NODES AND RETURNING A NODE OBJECT LIST
    textNodes: List[nuke.node] = nuke.allNodes('Text2')
    return textNodes


def renderContactSheet(readNode, outputFilePath, resolution, fileFormat, layers):
    """
    Render the contact sheet as per the user specification
        Args:
            readNode (Nuke Node) : User selected readnode from the node graph
            outputFilePath (str) : Render location path given by the user
            resolution(str) : Resolution selected by the user
            fileFormat(str) : Render file format selected by the user
            layers (List str) : List of render AOVs
    """

    #BREAKING OUT THE AOVs PRESENT IN THE SELECTED READ NODE
    textNodes = aovBreakout(readNode, layers)

    #CREATING A CONTACTSHEET NODE
    contactSheetNode = nuke.createNode('ContactSheet')
    aovCount = 0

    #CONNECTING THE INPUTS OF THE CONTACTSHEET NODE TO THE TEXT NODES
    for textNode in textNodes:
        contactSheetNode.setInput(aovCount, textNode)
        aovCount += 1
    
    #CALCULATING THE ROWS AND COLUMNS FOR THE CONTACTSHEET NODE SO THAT WE DON'T MISS OUT ON ANY AOVs
    rows = math.isqrt(aovCount)
    columns = math.isqrt(aovCount)+1
    if rows*columns >= aovCount:
        contactSheetNode['rows'].setValue(rows)
        contactSheetNode['columns'].setValue(columns) 
    else:
        contactSheetNode['rows'].setValue(rows+1)
        contactSheetNode['columns'].setValue(columns)
        
    #SETTING THE RESOLUTION OF THE CONTACTSHEET NODE
    if resolution == '2K':
        contactSheetNode['width'].setValue(2000)
        contactSheetNode['height'].setValue(2000)
    elif resolution == '4K':
        contactSheetNode['width'].setValue(4000)
        contactSheetNode['height'].setValue(4000)
    elif resolution == '6K':
        contactSheetNode['width'].setValue(6000)
        contactSheetNode['height'].setValue(6000)
    else:
        contactSheetNode['width'].setValue(8000)
        contactSheetNode['height'].setValue(8000)
        
    #SETTING UP THE WRITE NODE AND RENDERING THE CONTACTSHEET 
    writeNode = nuke.nodes.Write(label = 'Contact_Sheet_Output', inputs = [contactSheetNode])
    inputFilePath = readNode['file'].getValue()
    writeNode['file'].setValue(outputFilePath + inputFilePath.split('/')[-1].split('.')[0] + "_ContactSheet.%04d." + fileFormat.lower())
    writeNode['file_type'].setValue(fileFormat.lower())
    nuke.execute(writeNode, 1, 1, 1)
    

def contactSheetAttributes(readNode, layers):
    """
    Create another UI panel for the user to select resolution, file format and render location for the contactsheet render
        Args:
            readNode (Nuke Node) : User selected readnode from the node graph
            layers (List str) : List of render AOVs
    """
    #CREATING A PANEL UI FOR THE USER TO SELECT THE RESOLUTION AND FILE FORMAT
    contactSheetPanel = nuke.Panel("Render Contact Sheet")
    contactSheetPanel.addEnumerationPulldown('Resolution', '2K 4K 6K 8K')
    contactSheetPanel.addEnumerationPulldown('File Format', 'EXR PNG JPEG TIFF')
    if not contactSheetPanel.show():
        return
    
    #GETTING THE RENDER LOCATION FROM THE USER
    outputFilePath = nuke.getFilename('Select Render Location', '*.txt *.xml')
    
    #EXTRACTING THE CHOICES SELECTED BY THE USER
    resolution = contactSheetPanel.value('Resolution')
    fileFormat = contactSheetPanel.value('File Format')
    renderContactSheet(readNode, outputFilePath, resolution, fileFormat, layers)


def channelList():
    """
    Extract the channels out of the selected read node and formulate them into render AOVs
    """
    #EXTRACTING CHANNELS FROM SELECTED READ NODE
    readNode = nuke.selectedNode()
    channels = readNode.channels() 

    #COMBINING THE CHANNELS INTO AOVs
    layers = list(set([c.split('.')[0] for c in channels]))
    layers.sort()

    #CREATING A PANEL UI FOR THE USER TO SELECT THE DESIRED OPERATIONS FOR THE RENDERS
    aovPanel = nuke.Panel(f"Please select an opertion for {readNode.name()}")
    aovPanel.addEnumerationPulldown('Operation', 'RenderContactSheet AOVBreakout AutoCompSplit')
    if not aovPanel.show():
        return
    if aovPanel.value('Operation') == 'RenderContactSheet':
        contactSheetAttributes(readNode, layers)
    elif aovPanel.value('Operation') == 'AOVBreakout':
        aovBreakout(readNode, layers)
    elif aovPanel.value('Operation') == 'AutoCompSplit':
        mergeNodeName, globalDotNodeCount = autoCompSplit(readNode, layers)
        createCopyPremultNodes(readNode, mergeNodeName, globalDotNodeCount)