import os
import sys

try:
    import cnode
except Exception as exc:
    cnode_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../')
    sys.path.insert(0, cnode_path)
    import cnode

Service = cnode.cleinit()
from cnode.nodepoint import *
import libstarpy

class NodeManager(object):
    m_PCNodeManager = None
    def __init__(self, NodeSet,OutputClass=GeneralOutputClass):
        if NodeSet == None:
            raise Exception('please input NodeSet...')
        self.NodeSet = NodeSet
        self.OutputClass = OutputClass

    def NodeListKey(self,NodeList):
        result = '';
        for item in NodeList :
            result = result + item.GetKey();
        return result

    # wrap a python object to a node
    def ToNode(self,val,OutputClass=None,Name=None) :
        key = self.NodeSet.GetMD5(str(val))
        if self.NodeSet.LoadDefine(key) == False:
            if OutputClass == None :
                self.NodeSet.DefineNode(key, Name, 0,self.OutputClass)
            else :
                self.NodeSet.DefineNode(key, Name, 0,OutputClass)
        cle_obj = Service._New()
        cle_obj._AttachRawObject(val,False)
        node = self.NodeSet.CreateNode(key, cle_obj)
        if Name != None :
            node.SetLabel(Name)
        return node

    # get the wrapped python object
    def FromNode(self,node) :
        SrvGroup = libstarpy._GetSrvGroup(0)
        if SrvGroup._IsParaPkg(node) == True or type(node) == type(()) or type(node) == type([]) :
            result = []
            for item in node :
                if item.GetOwnerType() == 1:
                    if NodeManager.m_PCNodeManager == None:
                        from cnode.pcnode import PCNodeManager
                        NodeManager.m_PCNodeManager = PCNodeManager(self.NodeSet.GetPCRealm(),self.NodeSet)
                    result.append(NodeManager.m_PCNodeManager.FromNode(item))
                else :
                    attachobj = item.GetAttachObject()
                    if attachobj == None:
                        result.append(None)
                    else :
                        result.append( attachobj._GetRawObject())
            return result
        else :
            if node.GetOwnerType() == 1 :
                if NodeManager.m_PCNodeManager == None :
                    from cnode.pcnode import PCNodeManager
                    NodeManager.m_PCNodeManager = PCNodeManager(self.NodeSet.GetPCRealm(),self.NodeSet)
                return NodeManager.m_PCNodeManager.FromNode(node)
            attachobj = node.GetAttachObject()
            if attachobj == None :
                return None
            return attachobj._GetRawObject()

#internal class
class _NodePointControl(object):
    def __init__(self, NodePoint):
        self.NodePoint = NodePoint

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_trackback):
        return None

    # *args is list of nodes, as source node.
    def ConnectSource(self, *args):
        if len(args) == 0 :
            return self
        if self.NodePoint.GetNodeSet().BatchConnect(args,self.NodePoint.GetNode(),self.NodePoint.GetKey(),True) == False :
            raise Exception('connect nodes failed ')
        return self
 
class NodeControl(object):
    def __init__(self, NodeSet, NodeObject, OutputClass=GeneralOutputClass, InputClass = WhenAnyPointClass):
        self.NodeSet = NodeSet
        self.NodeObject = NodeObject
        self.OutputClass = OutputClass
        self.InputClass = InputClass
        if NodeSet == None or NodeObject == None :
            raise Exception('NodeSet and NodeObject must be valid ')
        self.NodeObject.CreateOutputPoint(self.OutputClass)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_trackback):
        if exc_trackback is None:
            self.NodeSet.SyncDefine(self.NodeObject.Key)
        return None

    def _WhenActive(self, func):
        if self.NodeObject == None:
            return
        self.NodeObject.SetCallOnActive(func)
    def WhenActive(self):
        def CreateDecorator(func):
            self._WhenActive(func)
        return CreateDecorator

    #create input point
    def Input(self, Key=None, InputClass = None, MaxSlotNumber=0,IsNegative=False,
                    IsNotCondition=False, IsDynamic=False):
        NodePoint = None
        if InputClass == None :
            NodePoint = self.NodeObject.CreateInputPoint(self.InputClass, Key, MaxSlotNumber,IsNegative,
                                    IsNotCondition, IsDynamic)
        else :
            NodePoint = self.NodeObject.CreateInputPoint(InputClass, Key, MaxSlotNumber,IsNegative,
                                    IsNotCondition, IsDynamic)
        if NodePoint == None :
            return
        else :
            return _NodePointControl(NodePoint)

#internal class
class _RelationControl_Create(object):
    def __init__(self, ChangeNodeList,name,NodeSet):
        '''
        ChangeNodeList : record the changed nodes
        name : Relation Name
        '''
        if name == '_' :
            self._name = NodeSet.GetMD5()
        else :
            self._name = name
        self.NodeSet = NodeSet
        self.ChangeNodeList = ChangeNodeList
    def __call__(self, *args,**kwargs):
        InputClass = WhenAnyPointClass
        MaxSlotNumber = 0
        IsNegative = False
        IsNotCondition = False
        IsDynamic = False
        for k,v in kwargs.items() :
            if k == 'InputClass':
                InputClass = v
            if k == 'MaxSlotNumber':
                MaxSlotNumber = v
            if k == 'IsNegative':
                IsNegative = v
            if k == 'IsNotCondition':
                IsNotCondition = v
            if k == 'IsDynamic':
                IsDynamic = v
        if len(args) == 2  :
            if self.NodeSet.IsNode(args[0]) == True :
                self.ChangeNodeList.append(args[0].Key)
                object_list = []
                if self.NodeSet.IsNode(args[1]) == True :     #Second parameter is a node
                    object_list = [[args[1],self._name]]
                    self.ChangeNodeList.append(args[1].Key)
                elif type(args[1]) == type(()) :              
                    for item in args[1]:
                        if self.NodeSet.IsNode(item) == False:
                            raise Exception('input must be node ')
                        self.ChangeNodeList.append(item.Key)
                        object_list.append([item, self._name])
                else :
                    raise Exception('input not supported')
                if self.NodeSet.BatchInputValid(object_list, InputClass, MaxSlotNumber, IsNegative,
                                                IsNotCondition, IsDynamic) == False:
                    raise Exception('create relation ' + self._name + ' failed, the input point can not created')
                self.NodeSet.CreateBatchInput(object_list, InputClass, MaxSlotNumber, IsNegative,
                                              IsNotCondition, IsDynamic)
                self.NodeSet.ConnectBatch(args[0],object_list)
            elif self.NodeSet.IsNode(args[1]) == True :      #First parameter is a node
                self.ChangeNodeList.append(args[1].Key)
                object_list = []
                if type(args[0]) == type(()) :
                    for item in args[0]:
                        if self.NodeSet.IsNode(item) == False:
                            raise Exception('input must be node ')
                        self.ChangeNodeList.append(item.Key)
                        object_list.append(item)
                else :
                    raise Exception('input not supported')
                if self.NodeSet.BatchInputValid([[args[1],self._name]], self.InputClass, self.MaxSlotNumber, self.IsNegative,
                                                self.IsNotCondition, self.IsDynamic) == False:
                    raise Exception('create relation ' + self._name + ' failed, the input point can not created')
                self.NodeSet.CreateBatchInput([[args[1],self._name]], self.InputClass, self.MaxSlotNumber, self.IsNegative,
                                              self.IsNotCondition, self.IsDynamic)
                self.NodeSet.BatchConnect(object_list,args[1],self._name)
        elif len(args) > 2  :
            raise Exception('input parameter error')

'''
with RelationControl(nodeset) as rc :
    rc._(node1,node2,node3)   #create a sequence relation : node1 -> node2 -> node3, relation name(input point key of node2/node3) is automatic generated 
    rc.support(node1,node2)   #create a relation : node1->node2,relation name(input point key of node2) is 'support'
    rc.support((node1,node2),node3)   #create two relation : node1->node3,and node2->node3, relation name(input point key of node3) is 'support'
    rc.support(node1,(node2,node3))   #create two relation : node1->node2,and node1->node3, name(input point key of node2/node3) is 'support'    
'''
#create relation : self.RelationName(SourceNode or SourceNodeList, TargtNode)
class RelationControl(object):
    def __init__(self, NodeSet, InputClass = WhenAnyPointClass,MaxSlotNumber=0,IsNegative=False,
                    IsNotCondition=False, IsDynamic=False):
        self.NodeSet = NodeSet
        self.InputClass = InputClass
        self.MaxSlotNumber = MaxSlotNumber
        self.IsNegative = IsNegative
        self.IsNotCondition = IsNotCondition
        self.IsDynamic = IsDynamic
        self.ChangeNodeList = []
        if NodeSet == None :
            raise Exception('NodeSet must be valid ')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_trackback):
        if exc_trackback is None:
            nodelist = list(set(self.ChangeNodeList))
            for item in nodelist :
                self.NodeSet.SyncDefine(item)
        return None

    # this function is dynamic
    def __getattr__(self, name):
        return _RelationControl_Create(self.ChangeNodeList,name,self.NodeSet)
