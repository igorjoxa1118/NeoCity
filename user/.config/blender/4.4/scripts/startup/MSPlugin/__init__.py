# ##### QUIXEL AB - MEGASCANS PLugin FOR BLENDER #####
#
# The Megascans Plugin  plugin for Blender is an add-on that lets
# you instantly import assets with their shader setup with one click only.
#
# Because it relies on some of the latest 4.0 features, this plugin is currently
# only available for Blender 4.0 and forward.
#
# You are free to modify, add features or tweak this add-on as you see fit, and
# don't hesitate to send us some feedback if you've done something cool with it.
#
# ##### QUIXEL AB - MEGASCANS PLUGIN FOR BLENDER #####

import bpy, threading, os, time, json, socket
from bpy.app.handlers import persistent

globals()['Megascans_DataSet'] = None

# This stuff is for the Alembic support
globals()['MG_Material'] = []
globals()['MG_AlembicPath'] = []
globals()['MG_ImportComplete'] = False

bl_info = {
    "name": "Megascans Plugin",
    "description": "Connects Blender to Quixel Bridge for one-click imports with shader setup and geometry",
    "author": "Quixel",
    "version": (3, 8, 0),
    "blender": (4, 0, 0),
    "location": "File > Import",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "https://docs.quixel.org/bridge/livelinks/blender/info_quickstart.html",
    "tracker_url": "https://docs.quixel.org/bridge/livelinks/blender/info_quickstart#release_notes",
    "support": "COMMUNITY",
    "category": "Import-Export"
}


# MS_Init_ImportProcess is the main asset import class.
# This class is invoked whenever a new asset is set from Bridge.

class MS_Init_ImportProcess():

    # This initialization method create the data structure to process our assets
    # later on in the initImportProcess method. The method loops on all assets
    # that have been sent by Bridge.
    def __init__(self):
        print("Initialized import class...")
        try:
            # Check if there's any incoming data
            if globals()['Megascans_DataSet'] != None:

                globals()['MG_AlembicPath'] = []
                globals()['MG_Material'] = []
                globals()['MG_ImportComplete'] = False

                self.json_Array = json.loads(globals()['Megascans_DataSet'])

                # Start looping over each asset in the self.json_Array list
                for js in self.json_Array:

                    self.json_data = js

                    self.selectedObjects = []
                    
                    self.IOR = 1.45
                    self.assetType = self.json_data["type"]
                    self.assetPath = self.json_data["path"]
                    self.assetID = self.json_data["id"]
                    self.isMetal = bool(self.json_data["category"] == "Metal")
                    # Workflow setup.
                    self.isHighPoly = bool(self.json_data["activeLOD"] == "high")
                    self.activeLOD = self.json_data["activeLOD"]
                    self.minLOD = self.json_data["minLOD"]
                    self.RenderEngine = bpy.context.scene.render.engine.lower() # Get the current render engine. i.e. blender_eevee or cycles
                    self.Workflow = self.json_data.get('pbrWorkflow', 'specular')
                    self.DisplacementSetup = 'regular'
                    self.isCycles = bool(self.RenderEngine == 'cycles')
                    self.isScatterAsset = self.CheckScatterAsset()
                    self.textureList = []
                    self.isBillboard = self.CheckIsBillboard()
                    self.ApplyToSelection = False
                    self.isSpecularWorkflow = True
                    self.isAlembic = False

                    self.NormalSetup = False
                    self.BumpSetup = False
                    
                    if "workflow" in self.json_data.keys():
                        self.isSpecularWorkflow = bool(self.json_data["workflow"] == "specular")

                    if "applyToSelection" in self.json_data.keys():
                        self.ApplyToSelection = bool(self.json_data["applyToSelection"])

                    if (self.isCycles):
                        if(bpy.context.scene.cycles.feature_set == 'EXPERIMENTAL'):
                            self.DisplacementSetup = 'adaptive'
                    
                    texturesListName = "components"
                    if(self.isBillboard):
                        texturesListName = "components"

                    # Get a list of all available texture maps. item[1] returns the map type (albedo, normal, etc...).
                    self.textureTypes = [obj["type"] for obj in self.json_data[texturesListName]]
                    self.textureList = []

                    for obj in self.json_data[texturesListName]:
                        texFormat = obj["format"]
                        texType = obj["type"]
                        texPath = obj["path"]

                        if texType == "displacement" and texFormat != "exr":
                            texDir = os.path.dirname(texPath)
                            texName = os.path.splitext(os.path.basename(texPath))[0]

                            if os.path.exists(os.path.join(texDir, texName + ".exr")):
                                texPath = os.path.join(texDir, texName + ".exr")
                                texFormat = "exr"
                        # Replace diffuse texture type with albedo so we don't have to add more conditions to handle diffuse map.
                        if texType == "diffuse" and "albedo" not in self.textureTypes:
                            texType = "albedo"
                            self.textureTypes.append("albedo")
                            self.textureTypes.remove("diffuse")

                        # Normal / Bump setup checks
                        if texType == "normal":
                            self.NormalSetup = True
                        if texType == "bump":
                            self.BumpSetup = True

                        self.textureList.append((texFormat, texType, texPath))

                    # Create a tuple list of all the 3d meshes  available.
                    # This tuple is composed of (meshFormat, meshPath)
                    self.geometryList = [(obj["format"], obj["path"]) for obj in self.json_data["meshList"]]

                    # Create name of our asset. Multiple conditions are set here
                    # in order to make sure the asset actually has a name and that the name
                    # is short enough for us to use it. We compose a name with the ID otherwise.
                    if "name" in self.json_data.keys():
                        self.assetName = self.json_data["name"].replace(" ", "_")
                    else:
                        self.assetName = os.path.basename(self.json_data["path"]).replace(" ", "_")
                    if len(self.assetName.split("_")) > 2:
                        self.assetName = "_".join(self.assetName.split("_")[:-1])

                    self.materialName = self.assetName + '_' + self.assetID
                    self.colorSpaces = ["sRGB", "Non-Color", "Linear"]
                    
                    print(f'Asset --> {self.assetType} -- {self.assetName}')
                    
                    # Initialize the import method to start building our shader and import our geometry
                    self.initImportProcess()
                    print("Imported asset from " + self.assetName + " Quixel Bridge")
        
            if len(globals()['MG_AlembicPath']) > 0:
                globals()['MG_ImportComplete'] = True        
        except Exception as e:
            print( "Megascans Plugin Error initializing the import process. Error: ", str(e) )
        
        globals()['Megascans_DataSet'] = None
    
    # this method is used to import the geometry and create the material setup.
    def initImportProcess(self):
        try:
            if len(self.textureList) >= 1:
                
                if(self.ApplyToSelection and self.assetType not in ["3dplant", "3d"]):
                    self.CollectSelectedObjects()

                self.ImportGeometry()
                self.CreateMaterial()
                self.ApplyMaterialToGeometry()
                if(self.isScatterAsset and len(self.selectedObjects) > 1):
                    self.ScatterAssetSetup()
                elif (self.assetType == "3dplant" and len(self.selectedObjects) > 1):
                    self.PlantAssetSetup()

                self.SetupMaterial()

                if self.isAlembic:
                    globals()['MG_Material'].append(self.mat)

        except Exception as e:
            print( "Megascans Plugin Error while importing textures/geometry or setting up material. Error: ", str(e) )

    def ImportGeometry(self):
        try:
            # Import geometry
            abcPaths = []
            if len(self.geometryList) >= 1:
                for obj in self.geometryList:
                    meshPath = obj[1]
                    meshFormat = obj[0]

                    if meshFormat.lower() == "fbx":
                        bpy.ops.import_scene.fbx(filepath=meshPath)
                        # get selected objects
                        obj_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
                        self.selectedObjects += obj_objects

                    elif meshFormat.lower() == "obj":
                        if bpy.app.version < (2, 92, 0):
                            bpy.ops.import_scene.obj(filepath=meshPath, use_split_objects = True, use_split_groups = True, global_clight_size = 1.0)
                        else:
                            bpy.ops.import_scene.obj(filepath=meshPath, use_split_objects = True, use_split_groups = True, global_clamp_size  = 1.0)
                        # get selected objects
                        obj_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
                        self.selectedObjects += obj_objects

                    elif meshFormat.lower() == "abc":
                        self.isAlembic = True
                        abcPaths.append(meshPath)
            
            if self.isAlembic:
                globals()['MG_AlembicPath'].append(abcPaths)
        except Exception as e:
            print( "Megascans Plugin Error while importing textures/geometry or setting up material. Error: ", str(e) )

    def dump(self, obj):
        for attr in dir(obj):
            print("obj.%s = %r" % (attr, getattr(obj, attr)))

    def CollectSelectedObjects(self):
        try:
            sceneSelectedObjects = [ o for o in bpy.context.scene.objects if o.select_get() ]
            for obj in sceneSelectedObjects:
                if obj.type == "MESH":
                    self.selectedObjects.append(obj)
        except Exception as e:
            print("Megascans Plugin Error::CollectSelectedObjects::", str(e) )

    def ApplyMaterialToGeometry(self):
        for obj in self.selectedObjects:
            # assign material to obj
            obj.active_material = self.mat

    def CheckScatterAsset(self):
        if('scatter' in self.json_data['categories'] or 'scatter' in self.json_data['tags'] or 'cmb_asset' in self.json_data['categories'] or 'cmb_asset' in self.json_data['tags']):
            return True
        return False

    def CheckIsBillboard(self):
        # Use billboard textures if importing the Billboard LOD.
        if(self.assetType == "3dplant"):
            if (self.activeLOD == self.minLOD):
                return True
        return False

    #Add empty parent for the scatter assets.
    def ScatterAssetSetup(self):
        bpy.ops.object.empty_add(type='ARROWS')
        emptyRefList = [ o for o in bpy.context.scene.objects if o.select_get() and o not in self.selectedObjects ]
        for scatterParentObject in emptyRefList:
            scatterParentObject.name = self.assetID + "_" + self.assetName
            for obj in self.selectedObjects:
                obj.parent = scatterParentObject
            break
    
    #Add empty parent for plants.
    def PlantAssetSetup(self):
        bpy.ops.object.empty_add(type='ARROWS')
        emptyRefList = [ o for o in bpy.context.scene.objects if o.select_get() and o not in self.selectedObjects ]
        for plantParentObject in emptyRefList:
            plantParentObject.name = self.assetID + "_" + self.assetName
            for obj in self.selectedObjects:
                obj.parent = plantParentObject
            break

    # def AddModifiersToGeomtry(self, geo_list, mat):
    #     for obj in geo_list:
    #         # assign material to obj
    #         bpy.ops.object.modifier_add(type='SOLIDIFY')

    #Shader setups for all asset types. Some type specific functionality is also handled here.
    def SetupMaterial (self):
        if "albedo" in self.textureTypes:
            if "ao" in self.textureTypes:
                self.CreateTextureMultiplyNode("albedo", "ao", -250, 300, -650, 450, -650, 150, 0, 1, True, "Base Color")
            else:
                self.CreateTextureNode("albedo", -650, 450, 0, True, "Base Color")
        
        if self.isSpecularWorkflow:
            if "specular" in self.textureTypes:
                self.CreateTextureNode("specular", -650, -1650, 0, True, "Specular IOR Level")
            
            if "gloss" in self.textureTypes:
                glossNode = self.CreateTextureNode("gloss", -640, -300,)
                invertNode = self.CreateGenericNode("ShaderNodeInvert", -250, -450)
                # Add glossNode to invertNode connection
                self.mat.node_tree.links.new(invertNode.inputs["Color"], glossNode.outputs["Color"])
                # Connect roughness node to the material parent node.
                self.mat.node_tree.links.new(self.nodes.get(self.parentName).inputs["Roughness"], invertNode.outputs["Color"])
            elif "roughness" in self.textureTypes:
                self.CreateTextureNode("roughness", -650, -450, 1, True, "Roughness")
        else:
            if "metalness" in self.textureTypes:
                self.CreateTextureNode("metalness", -650, -150, 1, True, "Metallic")
            
            if "roughness" in self.textureTypes:
                self.CreateTextureNode("roughness", -650, -450, 1, True, "Roughness")
            elif "gloss" in self.textureTypes:
                glossNode = self.CreateTextureNode("gloss", -650, -450,)
                invertNode = self.CreateGenericNode("ShaderNodeInvert", -250, -450)
                # Add glossNode to invertNode connection
                self.mat.node_tree.links.new(invertNode.inputs["Color"], glossNode.outputs["Color"])
                # Connect roughness node to the material parent node.
                self.mat.node_tree.links.new(self.nodes.get(self.parentName).inputs["Roughness"], invertNode.outputs["Color"])
            
        if "opacity" in self.textureTypes:
            self.CreateTextureNode("opacity", -650, -750, 1, True, "Alpha")
            self.mat.blend_method = 'HASHED'
        
        if "snow" in self.json_data["tags"] or "snow" in self.json_data["categories"]:
            if "transmission" in self.textureTypes:
                #print(f'Snow Asset --> {"snow" in self.json_data["tags"]} | {"snow" in self.json_data["categories"]} | Transmission: {"transmission" in self.textureTypes}')
                self.CreateTextureIntensityNode(-250, -1950, "transmission", True, "Transmission Weight", 'MULTIPLY', Value2 = 0.25)
            elif "translucency" in self.textureTypes:
                #print(f'Snow Asset --> {"snow" in self.json_data["tags"]} | {"snow" in self.json_data["categories"]} | Translucency: {"translucency" in self.textureTypes}')
                self.CreateTextureIntensityNode(-250, -1950, "translucency", True, "Transmission Weight", 'MULTIPLY', Value2 = 0.25)

        elif "translucency" in self.textureTypes:
            self.CreateTextureNode("translucency", -650, -1950, 0, True, "Transmission Weight")
                
        elif "transmission" in self.textureTypes:
            self.CreateTextureNode("transmission", -650, -1950, 1, True, "Transmission Weight")

        # If HIGH POLY selected > use normal_bump and no displacement
        # If LODs selected > use corresponding LODs normal + displacement
        if self.isHighPoly:
            self.BumpSetup = False
        self.CreateNormalNodeSetup(True, "Normal")

        if "displacement" in self.textureTypes and not self.isHighPoly:
            self.CreateDisplacementSetup(True)

    def CreateMaterial(self):
        self.mat = (bpy.data.materials.get( self.materialName ) or bpy.data.materials.new( self.materialName ))
        self.mat.use_nodes = True
        self.nodes = self.mat.node_tree.nodes
        self.parentName = "Principled BSDF"
        self.materialOutputName = "Material Output"

        self.mat.node_tree.nodes[self.parentName].distribution = 'MULTI_GGX'
        self.mat.node_tree.nodes[self.parentName].inputs["Metallic"].default_value = 1 if self.isMetal else 0 # Metallic value
        self.mat.node_tree.nodes[self.parentName].inputs["IOR"].default_value = self.IOR
        self.mat.node_tree.nodes[self.parentName].inputs["Specular IOR Level"].default_value = 0
        self.mat.node_tree.nodes[self.parentName].inputs["Coat Weight"].default_value = 0
        
        if "snow" in self.json_data["tags"] or "snow" in self.json_data["categories"]:
            self.mat.node_tree.nodes[self.parentName].subsurface_method = 'RANDOM_WALK'
            self.mat.node_tree.nodes[self.parentName].inputs["Subsurface Radius"].default_value = (0.4, 0.5, 0.6)
            self.mat.node_tree.nodes[self.parentName].inputs["Subsurface Scale"].default_value = (0.1)        
        
        self.mappingNode = None

        if self.isCycles and self.assetType not in ["3d", "3dplant"]:
            # Create mapping node.
            self.mappingNode = self.CreateGenericNode("ShaderNodeMapping", -1350, -900)
            self.mappingNode.vector_type = 'TEXTURE'
            # Create texture coordinate node.
            texCoordNode = self.CreateGenericNode("ShaderNodeTexCoord", -1700, -900)
            # Connect texCoordNode to the mappingNode
            self.mat.node_tree.links.new(self.mappingNode.inputs["Vector"], texCoordNode.outputs["UV"])

    def CreateTextureNode(self, textureType, PosX, PosY, colorspace = 1, connectToMaterial = False, materialInputIndex = ""):
        texturePath = self.GetTexturePath(textureType)
        textureNode = self.CreateGenericNode('ShaderNodeTexImage', PosX, PosY)
        textureNode.image = bpy.data.images.load(texturePath)
        textureNode.show_texture = True
        textureNode.image.colorspace_settings.name = self.colorSpaces[colorspace] # "sRGB", "Non-Color", "Linear"
        
        if textureType in ["albedo", "specular", "translucency"]:
            if self.GetTextureFormat(textureType) in "exr":
                textureNode.image.colorspace_settings.name = self.colorSpaces[2] # "sRGB", "Non-Color", "Linear"

        if connectToMaterial:
            self.ConnectNodeToMaterial(materialInputIndex, textureNode)
        # If it is Cycles render we connect it to the mapping node.
        if self.isCycles and self.assetType not in ["3d", "3dplant"]:
            self.mat.node_tree.links.new(textureNode.inputs["Vector"], self.mappingNode.outputs["Vector"])
        return textureNode
    
    
    def CreateTextureIntensityNode(self, PosX, PosY, textureType, connectToMaterial, materialInputIndex, Operation = 'ADD', Value1 = 0.5, Value2 = 0.5):
        trnsmTex_node = self.CreateTextureNode(textureType, -650, -1950, 1)
        mathNode = self.CreateGenericNode('ShaderNodeMath', PosX, PosY)
        mathNode.operation = Operation
        mathNode.inputs[0].default_value = Value1
        mathNode.inputs[1].default_value = Value2
        self.mat.node_tree.links.new(mathNode.inputs[0], trnsmTex_node.outputs["Color"])
        if connectToMaterial:
            self.ConnectNodeToMaterial(materialInputIndex, mathNode)
        self.ConnectNodeToMaterial("Subsurface Weight", trnsmTex_node)
        

    def CreateTextureMultiplyNode(self, aTextureType, bTextureType, PosX, PosY, aPosX, aPosY, bPosX, bPosY, aColorspace, bColorspace, connectToMaterial, materialInputIndex):
        #Add Color>MixRGB node, transform it in the node editor, change it's operation to Multiply and finally we colapse the node.
        multiplyNode = self.CreateGenericNode('ShaderNodeMixRGB', PosX, PosY)
        multiplyNode.blend_type = 'MULTIPLY'
        #Setup A and B nodes
        textureNodeA = self.CreateTextureNode(aTextureType, aPosX, aPosY, aColorspace)
        textureNodeB = self.CreateTextureNode(bTextureType, bPosX, bPosY, bColorspace)
        # Conned albedo and ao node to the multiply node.
        self.mat.node_tree.links.new(multiplyNode.inputs["Color1"], textureNodeA.outputs["Color"])
        self.mat.node_tree.links.new(multiplyNode.inputs["Color2"], textureNodeB.outputs["Color"])

        if connectToMaterial:
            self.ConnectNodeToMaterial(materialInputIndex, multiplyNode)

        return multiplyNode

    def CreateNormalNodeSetup(self, connectToMaterial, materialInputIndex):
        
        bumpNode = None
        normalNode = None
        bumpMapNode = None
        normalMapNode = None

        if self.NormalSetup and self.BumpSetup:
            bumpMapNode = self.CreateTextureNode("bump", -650, -1050)
            normalMapNode = self.CreateTextureNode("normal", -650, -1350)
            bumpNode = self.CreateGenericNode("ShaderNodeBump", -250, -1050)
            bumpNode.inputs["Strength"].default_value = 0.1
            normalNode = self.CreateGenericNode("ShaderNodeNormalMap", -250, -1350)
            # Add normalMapNode to normalNode connection
            self.mat.node_tree.links.new(normalNode.inputs["Color"], normalMapNode.outputs["Color"])
            # Add bumpMapNode and normalNode connection to the bumpNode
            self.mat.node_tree.links.new(bumpNode.inputs["Height"], bumpMapNode.outputs["Color"])
            if (2, 81, 0) > bpy.app.version:
                self.mat.node_tree.links.new(bumpNode.inputs["Normal"], normalNode.outputs["Normal"])
            else:
                self.mat.node_tree.links.new(bumpNode.inputs["Normal"], normalNode.outputs["Normal"])
            # Add bumpNode connection to the material parent node
            if connectToMaterial:
                self.ConnectNodeToMaterial(materialInputIndex, bumpNode)
        elif self.NormalSetup:
            normalMapNode = self.CreateTextureNode("normal", -650, -1350)
            normalNode = self.CreateGenericNode("ShaderNodeNormalMap", -250, -1350)
            # Add normalMapNode to normalNode connection
            self.mat.node_tree.links.new(normalNode.inputs["Color"], normalMapNode.outputs["Color"])
            # Add normalNode connection to the material parent node
            if connectToMaterial:
                self.ConnectNodeToMaterial(materialInputIndex, normalNode)
        elif self.BumpSetup:
            bumpMapNode = self.CreateTextureNode("bump", -650, -1050)
            bumpNode = self.CreateGenericNode("ShaderNodeBump", -250, -1050)
            bumpNode.inputs["Strength"].default_value = 0.1
            # Add bumpMapNode and normalNode connection to the bumpNode
            self.mat.node_tree.links.new(bumpNode.inputs["Height"], bumpMapNode.outputs["Color"])
            # Add bumpNode connection to the material parent node
            if connectToMaterial:
                self.ConnectNodeToMaterial(materialInputIndex, bumpNode)

    def CreateDisplacementSetup(self, connectToMaterial):
        if self.DisplacementSetup == "adaptive":
            # Add vector>displacement map node
            displacementNode = self.CreateGenericNode("ShaderNodeDisplacement", 100, -2250)
            displacementNode.inputs["Scale"].default_value = 0.1
            displacementNode.inputs["Midlevel"].default_value = 0
            # Add converter>RGB Separator node
            RGBSplitterNode = self.CreateGenericNode("ShaderNodeSeparateRGB", -250, -2250)
            # Import normal map and normal map node setup.
            displacementMapNode = self.CreateTextureNode("displacement", -650, -2250)
            # Add displacementMapNode to RGBSplitterNode connection
            self.mat.node_tree.links.new(RGBSplitterNode.inputs["Image"], displacementMapNode.outputs["Color"])
            # Add RGBSplitterNode to displacementNode connection
            self.mat.node_tree.links.new(displacementNode.inputs["Height"], RGBSplitterNode.outputs["R"])
            # Add normalNode connection to the material output displacement node
            if connectToMaterial:
                self.mat.node_tree.links.new(self.nodes.get(self.materialOutputName).inputs["Displacement"], displacementNode.outputs["Displacement"])
                self.mat.cycles.displacement_method = 'BOTH'

        if self.DisplacementSetup == "regular":
            pass        

    def ConnectNodeToMaterial(self, materialInputIndex, textureNode):
        self.mat.node_tree.links.new(self.nodes.get(self.parentName).inputs[materialInputIndex], textureNode.outputs[0])

    def CreateGenericNode(self, nodeName, PosX, PosY):
        genericNode = self.nodes.new(nodeName)
        genericNode.location = (PosX, PosY)
        return genericNode

    def GetTexturePath(self, textureType):
        for item in self.textureList:
            if item[1] == textureType:
                return item[2].replace("\\", "/")

    def GetTextureFormat(self, textureType):
        for item in self.textureList:
            if item[1] == textureType:
                return item[0].lower()

class ms_Init(threading.Thread):
    
	#Initialize the thread and assign the method (i.e. importer) to be called when it receives JSON data.
    def __init__(self, importer):
        threading.Thread.__init__(self)
        self.importer = importer

	#Start the thread to start listing to the port.
    def run(self):
        try:
            run_livelink = True
            host, port = 'localhost', 28888
            #Making a socket object.
            socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #Binding the socket to host and port number mentioned at the start.
            socket_.bind((host, port))

            #Run until the thread starts receiving data.
            while run_livelink:
                socket_.listen(5)
                #Accept connection request.
                client, addr = socket_.accept()
                data = ""
                buffer_size = 4096*2
                #Receive data from the client. 
                data = client.recv(buffer_size)
                if data == b'Bye Megascans':
                    run_livelink = False
                    break

                #If any data is received over the port.
                if data != "":
                    self.TotalData = b""
                    self.TotalData += data #Append the previously received data to the Total Data.
                    #Keep running until the connection is open and we are receiving data.
                    while run_livelink:
                        #Keep receiving data from client.
                        data = client.recv(4096*2)
                        if data == b'Bye Megascans':
                            run_livelink = False
                            break
                        #if we are getting data keep appending it to the Total data.
                        if data : self.TotalData += data
                        else:
                            #Once the data transmission is over call the importer method and send the collected TotalData.
                            self.importer(self.TotalData)
                            break
        except Exception as e:
            print( "Megascans Plugin Error initializing the thread. Error: ", str(e) )

class thread_checker(threading.Thread):
    
	#Initialize the thread and assign the method (i.e. importer) to be called when it receives JSON data.
    def __init__(self):
        threading.Thread.__init__(self)

	#Start the thread to start listing to the port.
    def run(self):
        try:
            run_checker = True
            while run_checker:
                time.sleep(3)
                for i in threading.enumerate():
                    if(i.getName() == "MainThread" and i.is_alive() == False):
                        host, port = 'localhost', 28888
                        s = socket.socket()
                        s.connect((host,port))
                        data = "Bye Megascans"
                        s.send(data.encode())
                        s.close()
                        run_checker = False
                        break
        except Exception as e:
            print( "Megascans Plugin Error initializing thread checker. Error: ", str(e) )
            pass

class MS_Init_LiveLink(bpy.types.Operator):

    bl_idname = "bridge.plugin"
    bl_label = "Megascans Plugin"
    socketCount = 0

    def execute(self, context):

        try:
            globals()['Megascans_DataSet'] = None
            self.thread_ = threading.Thread(target = self.socketMonitor)
            self.thread_.start()
            bpy.app.timers.register(self.newDataMonitor)
            return {'FINISHED'}
        except Exception as e:
            print( "Megascans Plugin Error starting blender plugin. Error: ", str(e) )
            return {"FAILED"}

    def newDataMonitor(self):
        try:
            if globals()['Megascans_DataSet'] != None:
                MS_Init_ImportProcess()
                globals()['Megascans_DataSet'] = None       
        except Exception as e:
            print( "Megascans Plugin Error starting blender plugin (newDataMonitor). Error: ", str(e) )
            return {"FAILED"}
        return 1.0


    def socketMonitor(self):
        try:
            #Making a thread object
            threadedServer = ms_Init(self.importer)
            #Start the newly created thread.
            threadedServer.start()
            #Making a thread object
            thread_checker_ = thread_checker()
            #Start the newly created thread.
            thread_checker_.start()
        except Exception as e:
            print( "Megascans Plugin Error starting blender plugin (socketMonitor). Error: ", str(e) )
            return {"FAILED"}

    def importer (self, recv_data):
        try:
            globals()['Megascans_DataSet'] = recv_data
        except Exception as e:
            print( "Megascans Plugin Error starting blender plugin (importer). Error: ", str(e) )
            return {"FAILED"}

class MS_Init_Abc(bpy.types.Operator):

    bl_idname = "ms_livelink_abc.py"
    bl_label = "Import ABC"

    def execute(self, context):

        try:
            if globals()['MG_ImportComplete']:
                
                assetMeshPaths = globals()['MG_AlembicPath']
                assetMaterials = globals()['MG_Material']
                
                if len(assetMeshPaths) > 0 and len(assetMaterials) > 0:

                    materialIndex = 0
                    old_materials = []
                    for meshPaths in assetMeshPaths:
                        for meshPath in meshPaths:
                            bpy.ops.wm.alembic_import(filepath=meshPath, as_background_job=False)
                            for o in bpy.context.scene.objects:
                                if o.select_get():
                                    old_materials.append(o.active_material)
                                    o.active_material = assetMaterials[materialIndex]
                                    
                        
                        materialIndex += 1
                    
                    for mat in old_materials:
                        try:
                            if mat is not None:
                                bpy.data.materials.remove(mat)
                        except:
                            pass

                    globals()['MG_AlembicPath'] = []
                    globals()['MG_Material'] = []
                    globals()['MG_ImportComplete'] = False

            return {'FINISHED'}
        except Exception as e:
            print( "Megascans Plugin Error starting MS_Init_Abc. Error: ", str(e) )
            return {"CANCELLED"}

@persistent
def load_plugin(scene):
    try:
        bpy.ops.bridge.plugin()
    except Exception as e:
        print( "Bridge Plugin Error::Could not start the plugin. Description: ", str(e) )

def menu_func_import(self, context):
    self.layout.operator(MS_Init_Abc.bl_idname, text="Megascans: Import Alembic Files")

def register():
    if len(bpy.app.handlers.load_post) > 0:
        # Check if trying to register twice.
        if "load_plugin" in bpy.app.handlers.load_post[0].__name__.lower() or load_plugin in bpy.app.handlers.load_post:
            return
    bpy.utils.register_class(MS_Init_LiveLink)
    bpy.utils.register_class(MS_Init_Abc)
    bpy.app.handlers.load_post.append(load_plugin)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    if len(bpy.app.handlers.load_post) > 0:
        # Check if trying to register twice.
        if "load_plugin" in bpy.app.handlers.load_post[0].__name__.lower() or load_plugin in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(load_plugin)
