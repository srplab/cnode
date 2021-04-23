<h1 align="center">CNodeSet</h1>

NodeSet manages a group of Nodes, defines and creates new Nodes, creates connection relationships between Nodes, sets Node status, captures changes in Node status, performs Node status updates, merges and creates NodeSet cascade

Define CNodeSet Type and Create Instance
------

**1. define CNodeSet type**

Create a new CNodeSet type by creating a CNodeSet object, setting a callback function

```python
MySetClass = Service.CNodeSetBase('MySetClass')

'''
#these functions may be not defined if the set does not interact with permanent storage 
@MySetClass._RegScriptProc_P('OnSaveDefine')
def OnSaveDefine(CleObj) :
  print('save to permanent storage')  
    
@MySetClass._RegScriptProc_P('OnLoadDefine')
def OnLoadDefine(CleObj,CNode, Key) :
  print('load node ',Key,' from permanent')   
  return False
  
@MySetClass._RegScriptProc_P('OnRemoveDefine')
def OnRemoveDefine(CleObj,Key) :
  print('remove node ',Key,' from permanent')     
  
@MySetClass._RegScriptProc_P('OnSaveParameter')
def OnSaveParameter(CleObj,Key,Para) :
  print('OnSaveParameter')     
  return False
  
@MySetClass._RegScriptProc_P('OnLoadParameter')
def OnLoadParameter(CleObj,Key,Para) :
  print('OnLoadParameter')     
  return False
 
'''   
```
For NodeSet, four callback functions need to be defined: OnSave, OnLoadDefine,etc. 'OnSave' is used to store the set to persistent media. 'OnLoadDefine' is used to load a Node from the persistent medium. 'OnRemoveDefine' is used to delete node from persistent medium.

**2. Create instance of CNodeSet**

```python
set = MySetClass()

or

set1 = set.CreateSet()
```

Create a next level NodeSet using CreateSet. 

**[At any time, you can create the next level Set and perform various processing on the new Set. Unless the Save function of the new Set is called, it will not affect the current Set](#)**

Functions supported by CNodeSet
------

#### a.Default output point class

*[SetOutputPointClass](#)*

`void SetOutputPointClass(void *OutputPointClass)`

*[GetOutputPointClass](#)*

`void *GetOutputPointClass()`

When defining the node type, if you do not specify the output node type, the default type here is used

#### b.Node functions

*[DefineNode](#)*

Defines the node type. If the same Key already exists in the previous Set, the function fails.

`VS_BOOL DefineNode(VS_CHAR *CNodeKey,VS_CHAR *CNodeLabel,VS_INT32 CNodeOwnerType,void *OutputPointClass)`

OwnerType is set when DefineNode, 0 and 1 are reserved, the meaning is interpreted externally

CNodeLabel is a string for easy reading

if OutputPointClass is NULL, using DefaultOutputPointClass which is set via SetOutputPointClass

*[RemoveDefine](#)*

Deleting a node type definition affects the current set. When the current set is stored, it affects the previous set.

`void RemoveDefine(VS_CHAR *CNodeKey)`

*[CreateDefInput](#)*

If it already exists, and the parameters are the same, it returns success, otherwise it displays a warning message and returns NULL.

`VS_BOOL CreateDefInput(VS_CHAR *CNodeKey, void *InputPointClass, VS_CHAR *InputPointKey,VS_INT32 MaxSlotNumber,VS_BOOL IsNegative,VS_BOOL IsNotCondition,VS_BOOL IsDynamic)`

MaxSlotNumber = 0 means no limit

**[If IsNegative is true, the node should be inactive when the input point is activated](#)**

**[If IsNotCondition is true, the input node point's ConditionFlag will be set to false, then when calculating the output, it should not be taken into account, and the intermediate node of Node should not be connected to it.](#)**

**[If IsDynamic is equal to True, then input point need not save or merge. It's connections are valid for itself](#)**

**[InputPointKey maybe NULL or empty string](#)**

*[HasDefInput](#)*

`VS_BOOL HasDefInput(VS_CHAR *CNodeKey, VS_CHAR *InputPointKey)`

*[RemoveDefInput](#)*

`VS_BOOL RemoveDefInput(VS_CHAR *CNodeKey, VS_CHAR *InputPointKey)`

*[GetDefInputClass](#)*

`void *GetDefInputClass(VS_CHAR *CNodeKey, VS_CHAR *InputPointKey)`

*[GetDefInputMaxSlotNumber](#)*

`VS_INT32 GetDefInputMaxSlotNumber(VS_CHAR *CNodeKey, VS_CHAR *InputPointKey)`

*[GetDefInputNegativeFlag](#)*

NegativeFlag can be true or false, usually false, which means that when the point is activated, it supports the activation of the owning node. If it is true, when the point is activated, it opposes the activation of the owning node.

`VS_BOOL GetDefInputNegativeFlag(VS_CHAR *CNodeKey, VS_CHAR *InputPointKey)`

*[GetDefInputConditionFlag](#)*

`VS_BOOL GetDefInputConditionFlag(VS_CHAR *CNodeKey, VS_CHAR *InputPointKey)`

If it is equal to False, then when calculating the output, it should not be taken into account, and the intermediate node of Node should not be connected to the node whose Condition is equal to False.

*[GetDefInputDynamicFlag](#)*

`VS_BOOL GetDefInputDynamicFlag(VS_CHAR *CNodeKey, VS_CHAR *InputPointKey)`

If it is equal to true, indicates that the relationship is dynamic, temporary, and need not save.

*[GetDefInput/GetDefInputEx](#)*

Get input point of node from key

`void *GetDefInput(VS_CHAR *CNodeKey, VS_CHAR *InputPointKey)`

`VS_PARAPKGPTR GetDefInputEx(VS_CHAR *CNodeKey,void *InputPointClass)`

*[GetDefInputKey](#)*

`VS_PARAPKGPTR GetDefInputKey(VS_CHAR *CNodeKey))`

*[GetDefTargetNodeKey](#)*

`VS_PARAPKGPTR GetDefTargetNodeKey(VS_CHAR *SourceNodeKey, VS_CHAR *DestPointKey)`

Get the key of target nodes. If DestPointKey is null or empty string, all target nodes are returned, or else, the target node which input point is DestPointKey is returned.

*[SetDefParameter](#)*

Set the Parameter. The input value maybe bool, int, double, parapkg or string. If Value is NULL, then the parameter will be removed

`VS_BOOL SetDefParameter(VS_CHAR *CNodeKey, VS_CHAR *Key, void *Value)`

*[GetDefParameter/DefParameter](#)*

Get the Parameter. The return value maybe bool, int, double, parapkg or string

`void* GetDefParameter(VS_CHAR *CNodeKey, VS_CHAR *Key)`

`VS_PARAPKGPTR DefParameter(VS_CHAR *CNodeKey)`

*[GetDefParameterKey](#)*

`VS_PARAPKGPTR GetDefParameterKey()`

*[CreateDefRelation](#)*

`VS_BOOL CreateDefRelation(VS_CHAR *SourceNodeKey, VS_CHAR *DestNodeKey, VS_CHAR *DestPointKey,VS_CHAR *SlotID)`

This function does not establish a direct connection to the node. If it already exists, return true.

SlotID is MD5 string, and may be NULL or empty string.

*[RemoveDefRelation](#)*

`void RemoveDefRelation(VS_CHAR *SourceNodeKey, VS_CHAR *DestNodeKey, VS_CHAR *DestPointKey)`

SlotID is MD5 string, and may be NULL or empty string. If SlotID is empty string or NULL, this function deletes all relations of the same Key for the source and destination.

*[GetDefSlotID](#)*

`VS_PARAPKGPTR GetDefSlotID(VS_CHAR *SourceNodeKey, VS_CHAR *DestNodeKey, VS_CHAR *DestPointKey)`

*[AllocDefSlotID](#)*

This function first finds the existing SlotID that is not in ExcudeSlotID, if not, assigns a new ID.

`VS_CHAR *AllocDefSlotID(VS_CHAR *SourceNodeKey, VS_CHAR *DestNodeKey, VS_CHAR *DestPointKey,VS_PARAPKGPTR ExcudeSlotID)`

*[HasDefRelation](#)*

`VS_BOOL HasDefRelation(VS_CHAR *SourceNodeKey, VS_CHAR *DestNodeKey, VS_CHAR *DestPointKey)`

*[SetDefRelationParameter](#)*

`VS_BOOL SetDefRelationParameter(VS_CHAR *SourceNodeKey, VS_CHAR *DestNodeKey, VS_CHAR *DestPointKey, VS_CHAR *SlotID, VS_CHAR *RelationKey,void *RelationParameter))`

The RelationParameter can be integer, bool, string, floating point, or ParaPkg. If RelationParameter is NULL, the RelationKey will be removed

SlotID is MD5 string. And may be NULL or empty string, in this case, if there are multiple relationships with the same Key, set to the same value

*[GetDefRelationParameter](#)*

`void *GetDefRelationParameter(VS_CHAR *SourceNodeKey, VS_CHAR *DestNodeKey, VS_CHAR *DestPointKey, VS_CHAR *SlotID, VS_CHAR *RelationKey)`

SlotID is MD5 string. And may be NULL or empty string, in this case, if there are multiple relationships with the same Key, the first one is returned

The returned type is related to the parameter type, which can be integer, bool, string, floating point, or ParaPkg. If Key does not exist, None is returned.

*[RemoveDefRelationParameter](#)*

`VS_BOOL RemoveDefRelationParameter(VS_CHAR *SourceNodeKey, VS_CHAR *DestNodeKey, VS_CHAR *DestPointKey, VS_CHAR *SlotID, VS_CHAR *RelationKey)`

SlotID is MD5 string. And may be NULL or empty string, in this case, if there are multiple relationships with the same key, their key-values are all deleted

*[DefRelationParameter](#)*

`VS_PARAPKGPTR DefRelationParameter(VS_CHAR *SourceNodeKey, VS_CHAR *DestNodeKey, VS_CHAR *DestPointKey, VS_CHAR *SlotID)`

*[HasDefRelationParameter](#)*

`VS_BOOL HasDefRelationParameter(VS_CHAR *SourceNodeKey, VS_CHAR *DestNodeKey, VS_CHAR *DestPointKey, VS_CHAR *SlotID, VS_CHAR *RelationKey)`

*[GetDefRelationParameterKey](#)*

`VS_PARAPKGPTR GetDefRelationParameterKey(VS_CHAR *SourceNodeKey, VS_CHAR *DestNodeKey, VS_CHAR *DestPointKey, VS_CHAR *SlotID)`

SlotID is MD5 string. And may be NULL or empty string, in this case, if there are multiple relationships with the same Key, the first one is returned

*[FindDefine](#)*

Whether the node type exists in the current Set

`VS_BOOL FindDefine(VS_CHAR *CNodeKey)`

*[LoadDefine](#)*

Whether the node type exists in the current set. If it does not exist, it will be loaded from the upper level set. If the upper level does not exist, return false.

`VS_BOOL LoadDefine(VS_CHAR *CNodeKey)`

*[GetDefine](#)*

Get Node Type Definition

`void *GetDefine(VS_CHAR *CNodeKey)`

*[GetDefineInst/GetDefineActiveInst](#)*

Get all instances of Node

`VS_PARAPKGPTR GetDefineInst(VS_CHAR *CNodeKey)`

`VS_PARAPKGPTR GetDefineActiveInst(VS_CHAR *CNodeKey)`

*[GetDefineList](#)*

Get all Node types in the current Set

`VS_PARAPKGPTR GetDefineList()`

*[FindNode](#)*

Find the node which associated with AttachObject. AttachObject must not be NULL

`void *FindNode(VS_CHAR *CNodeKey,void *AttachObject)`

*[RemoveNode](#)*

`void RemoveNode(void *CNode)`

*[GetNodeList](#)*

Get all nodes in the current Set

`VS_PARAPKGPTR GetNodeList()`

*[CreateNode](#)*

> If AttachObject is not NULL
>> * the node associated with it returned if existed. else,
>> * create a new node

> If AttachObject is NULL
>> * create a new node

`void *CreateNode(VS_CHAR *CNodeKey, void *AttachObject)`

**[If the node type does not exist, it is loaded from the previous set and the OnLoadDefine callback is used](#)**

*[AllocTargetNode](#)*

If there is a node exists and has an empty slot that can connect to the SourceNode, the Node is returned, otherwise a new Node is created

`void *AllocTargetNode(void *SourceNode, VS_CHAR *DestNodeKey, VS_CHAR *DestPointKey)`

**[If the node type does not exist, it is loaded from the previous set and the OnLoadDefine callback is used](#)**

#### c.Relations functions

After adding, deleting, modifying or connecting the source node, you can use this function to train NodePoint and modify the weight.

*[GetRelationID](#)*

`VS_PARAPKGPTR GetRelationID(void *SourceNode, void *DestNode, VS_CHAR *DestPointKey)`

RelationID is SlotID of DestPoint, which SourceNode connected.

*[AllocRelationID](#)*

This function first finds the existing (RelationID)SlotID which is not connected, and is not in ExcudeSlotID, if not, assigns a new ID.

`VS_CHAR *AllocRelationID(void *SourceNode, void *DestNode, VS_CHAR *DestPointKey, VS_PARAPKGPTR ExcudeSlotID)`

*[CreateRelation](#)*

**After the relationship is created or deleted, the input points of the target node can be trained through Node's function Train**

**CreateRelation will establish a connection. If SlotID is valid and the corresponding input point is already connected, the current connection is deleted and a new connection is established.**

If SlotID is valid and not existed in the corresponding input point, new source point will be added for input point.

**[SlotID maybe NULL or empty string. In this case,if the NodePoint is already connected to other nodes and has no empty slots, this function will disconnect the current connection for new.To avoid this situation, you can use the DisConnect function to release the slot first.](#)**

`VS_BOOL CreateRelation(void *SourceNode, void *DestNode, VS_CHAR *DestPointKey, VS_CHAR *SlotID)`

for example,

```python
set.CreateRelation(None,node1,node2,'in1')
```

**[When creating a relationship, do not set the key-value related to the relationship, which makes this function more widely applicable, because the key-value is more used for network calculations, rather than explaining the meaning of the relationship](#)**

**[You can create key-values and set random values for all source nodes in InitSourceValueByKey in the OnExecute callback function of NodePoint](#)**

**If DestPointKey is equal to NULL or the length is 0, then a MD5 string is assigned as the point key**

*[CreateBatchRelation](#)*

`VS_BOOL CreateBatchRelation(VS_PARAPKGPTR SourceNodeList, void *DestNode, VS_CHAR *DestPointKey)`

**If DestPointKey is equal to NULL or the length is 0, then a MD5 string is assigned as the point key**

**CreateBatchRelation/CreateBatchRelationEx will establish a connection. Empty slot of the corresponding input point will be used. If there is no empty slot, new source point will be added for input point..**

*[RemoveRelation](#)*

`void RemoveRelation(void *SourceNode, void *DestNode, VS_CHAR *DestPointKey)`

*[HasRelation](#)*

`VS_BOOL HasRelation(void *SourceNode, void *DestNode, VS_CHAR *DestPointKey)`

Return false if not connected

*[HasRelationEx](#)*

Two node has relations or not. Return false if not connected

`VS_BOOL HasRelationEx(void *SourceNode, void *DestNode)`

#### c.1 Input pattern functions

*[CreateDefInputPattern](#)*

This function creates a pattern for the input points of DynamicFlag = false, which is used to judge the validity of the input and actively obtain the input.

`VS_BOOL CreateDefInputPattern(VS_CHAR *CNodeKey, VS_CHAR *InputPointKey, void *PatternClass);`

*[RemoveDefInputPattern](#)*

Delete the pattern.

`void RemoveDefInputPattern(VS_CHAR *CNodeKey, VS_CHAR *InputPointKey, void *Pattern)`

*[GetDefInputPattern](#)*

Get all the patterns defined by the input point.

`VS_PARAPKGPTR GetDefInputPattern(VS_CHAR *CNodeKey, VS_CHAR *InputPointKey)`


#### d.Inference related functions

*[ActiveNode/ActiveBatchNode](#)*

Active node activation. if NotExpadNode is false, the target node will be loaded automatically.

`VS_BOOL ActiveNode(void *CNode)`

`VS_BOOL ActiveBatchNode(VS_PARAPKGPTR CNodeList)`

*[IsNodeActive](#)*

the output of node is valid and greater than CNODE_ACTIVE_MINVALUE

`VS_BOOL IsNodeActive(void *CNode)`

*[CreateRunner](#)*

Create the CNodeRunner object.

`void *CreateRunner(void *RunnerClass)`

*[SetRunner](#)*

Set the runner which is created by other mean.

`void SetRunner(void *Runner)`

*[CurrentRunner](#)*

Get the current runner object, If the function is not called in the Runner process, it may return NULL.

`void *CurrentRunner()`

*[CreateEvent](#)*

Create a NodeEventClass instance which does not exist, and add it to the set.

`void *CreateEvent(void *NodeEventClass)`

*[RemoveEvent](#)*

Remove a NodeEventClass instance from the set.

`VS_BOOL RemoveEvent(void *NodeEventClass)`

*[GetEvent](#)*

Get CNodeEventeBase Objects of the set.

`VS_PARAPKGPTR GetEvent()`

*[GetDefaultEvent](#)*

Get Default Event list which the set supports.

`VS_PARAPKGPTR GetDefaultEvent()`

The return value will be as [[EventName(string),EventCode(int)],...]

```
#define CNODE_EVENTCODE_BEFORETURN 1
#define CNODE_EVENTNAME_BEFORETURN "Before Turn"
#define CNODE_EVENTCODE_AFTERTURN  2
#define CNODE_EVENTNAME_AFTERTURN  "After Turn"
```

*[FireEvent](#)*

The EventCode must be bigger than 127.

`VS_BOOL FireEvent(VS_UINT32 EventCode)`

In this function, the NodeRuleBase Object's OnExecute will be called.

**[Default event is managed by the cnode. Do not call this function to fire default event](#)**

*[GetRelateCount](#)*

Get the relation count of the node.

`VS_INT32 GetRelateCount(void *CNode)`

*[GetRelateNode](#)*

Get all inactive nodes related to the input node (unless IncludeActiveNode is True), sorted by relationship count from big to small.

**[If VS_BOOL BackwordFlag is false, only forward relationship nodes are returned; if true, only backward relationship nodes are returned](#)**

`VS_PARAPKGPTR GetRelateNode(VS_PARAPKGPTR AttentionNodeList,VS_BOOL BackwordFlag,VS_BOOL IncludeActiveNode)`

The return value is list of set, such as [[node,RelateCount],...]

*[ExtractActive](#)*

Get active nodes from input node list

`VS_PARAPKGPTR ExtractActive(VS_PARAPKGPTR NodeList)`

*[GetActive](#)*

Get all active nodes in the set.

`VS_PARAPKGPTR GetActive()`

*[CanAsSource](#)*

Get a list of all nodes that can be used as input nodes. If NodePointKey is equal to NULL, get all source nodes

`VS_PARAPKGPTR CanAsSource(void *CNode, VS_CHAR *NodePointKey, VS_BOOL MustActive)`

*[CanAsTarget](#)*

Get a list of all nodes that can be used as target node. 

If MustHasEmptySlot true, the CNode must has empty target slot.

`VS_PARAPKGPTR CanAsTarget(void *CNode, VS_CHAR *NodePointKey, VS_BOOL MustActive,VS_BOOL MustHasEmptySlot)`

*[DeactiveNode/DeactiveBatchNode](#)*

Deactive the node, that is, the output value is set to 0.0.

`VS_BOOL DeactiveNode(void *CNode)`

`VS_BOOL DeactiveBatchNode(VS_PARAPKGPTR CNodeList)`

*[Reset](#)*

`void Reset()`

*[GetPerformTick](#)*

Get the current schedule tick.

`VS_INT64 GetPerformTick()`


#### e.Node expansion function

*[ExpandSource](#)*

Load the source node.

`VS_BOOL ExpandSource(void *CNode, VS_CHAR *InputPointKey)`

InputPointKey maybe NULL or empty string, in this case, ExpandSource for all input points.

*[ExpandTarget](#)*

Load the target node.

`VS_BOOL ExpandTarget(void *CNode)`

#### f.Save functions

*[SaveDefine](#)*

To save the node's define in current set, the callback function OnSaveDefine will be called.

`VS_BOOL Save(VS_BOOL SaveToStorage)`

If SaveToStorage is false, this function only merge node to node define and not trigger OnSaveDefine callback.

*[SyncDefine](#)*

When the Node changes, call this function to store the changes to the Node Define. This function does not store Node to storage.

`VS_BOOL SyncDefine(VS_CHAR *CNodeKey)`

*[Merge](#)*

Calling this function will not cause the node definition to be deleted

`VS_BOOL Merge(void *SourceNodeSet)`

*[SaveNodeToString](#)*

Save all nodes in the Set, including connections between nodes

`VS_CHAR *SaveNodeToString()`

*[LoadNodeFromString](#)*

Restore all nodes from a string, and connections between nodes. The function should be called in the newly created empty set

`VS_BOOL LoadNodeFromString(VS_CHAR *SaveValue)`

*[SaveDefToString](#)*

Save all node's define in the Set.

`VS_CHAR *SaveDefToString()`

*[LoadDefFromString](#)*

Restore all node define from a string. If the node's key has existed, it will be replaced by newer.

`VS_BOOL LoadDefFromString(VS_CHAR *SaveValue))`

#### g.Callback functions

*[OnSaveDefine](#)*

`VS_BOOL OnSaveDefine()`

Store Node define to persistent storage.

If the NodeSet has key, the key must be saved when it's Nodes is saved.

```python
@MySetClass._RegScriptProc_P('OnSaveDefine')
def OnSaveDefine(CleObj) :
  # get the node list
  nodelist = CleObj.GetDefineList()
  for node in nodelist :
    # get the node key for index in persistent storage
    key = node.GetKey()
    # get node key value pair, and save or update
    value_keys = node.GetParameterKey()
    # save or update AttachValue(node.GetAttachValue()), if not empty
    # save or update target(node.GetTarget())
    # save or update ouput point(node.GetOutputPoint())
    # save or update input point(node.GetInputPoint())
```

*[OnLoadDefine](#)*

`VS_BOOL OnLoadDefine(void *CNode,VS_CHAR *CNodeKey)`

Load load from persistent storage

```python
@MySetClass._RegScriptProc_P('OnLoadDefine')
def OnLoadDefine(CleObj,CNode,Key) :
  # find node by key from persistent storage
  # load node key-value, and set to node with 'SetDefParameter'
  # load AttachValue
  # load target
  # load output point
  # load input point
  return True/False
```

*[OnRemoveDefine](#)*

`void OnRemoveDefine(VS_CHAR *CNodeKey)`

Delete node from persistent storage

```python
@MySetClass._RegScriptProc_P('OnRemoveDefine')
def OnRemoveDefine(CleObj,Key) :
  print('remove node ',Key,' from permanent') 
```

**[If you don't use persistent storage, the above callback function does not need to be defined](#)**

#### h.Copy or Remove input point

*[DupInputPoint](#)*

This function copies the input points of the node and adds it to the node. At the same time, the target point of the source node is inserted for the new input point key. The copied input points can use different NodePoint types to optimize the structure of the Node.

`void *DupInputPoint(void *CNode, VS_CHAR *PointKey, void *NewInputPointClass, VS_CHAR *NewPointKey)`

*[RemoveInputPoint](#)*

This function delete the input point of the node. At the same time, the target point of the source node is removed too. 

`void RemoveInputPoint(void *CNode, VS_CHAR *PointKey)`

#### h.Execute function

*[Execute](#)*

This function calls OnExecute callback of each NodeRunner object

`VS_PARAPKGPTR Execute()`

The return result is the newly activated object of each runner, such as, [[runner1,[node,...],[runner2,[node,...],...]

*[ExecuteIssue](#)*

`VS_BOOL ExecuteIssue(struct StructOfCNodePointBase *CNodePoint,VS_INT32 Reason)`

The CNodePoint must be output point of node.

Reason :

> * 1: CNODE_EXECUTE_CONFLICT
> * 2: CNODE_EXECUTE_NOOUTPUT, can not generate output
> * 4: CNODE_EXECUTE_UNBIND, there has input unbind
> * 8: CNODE_EXECUTE_BINDMORE, too more input are bind
> * 16: CNODE_EXECUTE_NEEDINPUT, need more node.
> * 128: CNODE_EXECUTE_FAILED, When the output node can execute but cannot determine how to execute, this function may be called. There are many reasons why it cannot be executed. For example, too many input parameters make it impossible to determine how to execute.

*[SetIssueBuf](#)*

Set new issue buf, and returns the old buf.

`VS_PARAPKGPTR SetIssueBuf(VS_PARAPKGPTR IssueBuf)`

#### i.connect functions

*[ConnectBatch](#)*

Connect CNode to multiple target nodes

`VS_BOOL ConnectBatch(void *CNode, VS_PARAPKGPTR TargetNodeObjectWithInputKeyList,VS_BOOL Connect)`

if Connect is false, the function only create relations and does not connect them

*[ConnectBatchEx](#)*

Setup relations between CNodeKey and multiple target nodes. not connect.

`VS_BOOL ConnectBatchEx(VS_CHAR *CNodeKey, VS_PARAPKGPTR TargetNodeKeyWithInputKeyList)`

*[BatchConnect](#)*

Connect multiple nodes to TargetNode and TargetPointKey

`VS_BOOL BatchConnect(VS_PARAPKGPTR NodeObjectList, void *TargetNode, VS_CHAR *TargetPointKey,VS_BOOL Connect)`

input is node object list, not including input point key

if Connect is false, the function only create relations and does not connect them

*[BatchConnectEx](#)*

Setup relations between multiple nodes and TargetNode and TargetPointKey. not connect.

`VS_BOOL BatchConnectEx(VS_PARAPKGPTR NodeKeyList, VS_CHAR *TargetNodeKey, VS_CHAR *TargetPointKey)`

input is node key list, not including input point key

*[BatchInputValid](#)*

The input point of each node can be created or has existed.

`VS_BOOL BatchInputValid(VS_PARAPKGPTR NodeObjectWithInputKeyList, void *InputPointClass, VS_INT32 MaxSlotNumber, VS_BOOL IsNegative, VS_BOOL IsNotCondition, VS_BOOL IsDynamic)`

The format of NodeObjectWithInputKeyList is [[cnode,inputpointkey],...]

*[CreateBatchInput](#)*

Create input point of each node.

`VS_BOOL CreateBatchInput(VS_PARAPKGPTR NodeObjectWithInputKeyList, void *InputPointClass, VS_INT32 MaxSlotNumber, VS_BOOL IsNegative, VS_BOOL IsNotCondition, VS_BOOL IsDynamic)`

#### j.Other functions

*[SetLabel](#)*

`void SetLabel(VS_CHAR *Label)`

*[GetLabel](#)*

`VS_CHAR *GetLabel()`

*[SetKey](#)*

The key can only be set to the NodeSet which has no BasicSet. The length of Key must be less than the value returned by GetMaxKeyLength. If the NodeSet has key, the key must be saved when it's Nodes is saved.

`VS_BOOL SetKey(VS_CHAR *Key)`

*[GetKey](#)*

`VS_CHAR *GetKey()`

*[SetAutoExpand](#)*

**[When ActiveNode / ActiveBatchNode / GetRelateNode / GetRelateCount is called, the target object is automatically loaded and connected. Default is true](#)**

`void SetAutoExpand(VS_BOOL IsAutoExpand)`

*[GetAutoExpand](#)*

`VS_BOOL GetAutoExpand()`

*[SetParameter](#)*

Set the Parameter. The input value maybe bool, int, double, parapkg or string. If Value is NULL, then the parameter will be removed

`VS_BOOL SetParameter(VS_CHAR *Name, void *Value)`

*[GetParameter/Parameter](#)*

Get the Parameter. The return value maybe bool, int, double, parapkg or string

`void *GetParameter(VS_CHAR *Name)`

`VS_PARAPKGPTR Parameter()`

*[GetParameterKey](#)*

`VS_PARAPKGPTR GetParameterKey()`

*[CreateSet](#)*

Create a new NodeSet based on this

`void *CreateSet()`

*[CopyNodeToNew](#)*

This function creates a new NodeSet and copy Node, and copy all its connected source nodes into the new Set if CopyAllSourceConnected is true.

Return value is the new NodeSet.

`void *CopyNodeToNew(void *CNode,VS_BOOL CopyAllSourceConnected)`

*[CopyNodeToNewEx](#)*

Create a Set, copy the CNode, and all its connected active source nodes, the connected active source nodes of the source node, until the output of the node is set externally.

Return value is the new NodeSet.

`void *CopyNodeToNewEx(void *CNode)`

*[IsNode](#)*

Input object is CNode or not.

`VS_BOOL IsNode(void *CNode)`

*[GetMaxKeyLength](#)*

Get the Node or NodePoint key length

`VS_INT32 GetMaxKeyLength()`

*[IsRootNodeSet](#)*

The Root NodeSet is not created by CreateSet. Its BasicNodeSet is NULL. When the RootNodeSet is stored, the OnSave callback function is triggered

`VS_BOOL IsRootNodeSet()`

*[GetRootNodeSet](#)*

`void *GetRootNodeSet()`

*[PrintNode](#)*

print node's source and target nodes. if PrintNodeDefine is true, print node define, or else print node isntance.

`void PrintNode(VS_BOOL PrintNodeDefine)`

*[GetMD5](#)*

Get MD5 of input string.

`VS_CHAR *GetMD5(VS_CHAR *Info)`

*[PrintInfo](#)*

`void PrintInfo(VS_CHAR *Info)`

*[PrintWarning](#)*

`void PrintWarning(VS_CHAR *Info)`

If Info is NULL or empty string, the funtion create new MD5 string.

#### k.Save parameter callback

*[OnSaveParameter](#)*

`VS_BOOL OnSaveParameter(VS_CHAR *Key, VS_PARAPKGPTR Para)`

*[OnLoadParameter](#)*

`VS_BOOL OnLoadParameter(VS_CHAR *Key, VS_PARAPKGPTR Result)`

#### l.PCRealm Object

*[SetPCRealm](#)*

`void SetPCRealm(void *Realm)`

*[GetPCRealm](#)*

`void *GetPCRealm()`

#### m.Reader functions

ReaderObjects provides a convenient way to read NodeSet/Node/NodePoint/Slot's properties. For example,

```python
  a = CNodeSet.GetNodePointReader(None,CNodePoint)
  print(a.Key)
  print(a.Node)
  print(a.Node.Key)
  print(a.Node.XXXXX)
```  

*[SetSlotReaderClass/SetNodePointReaderClass/SetNodeReaderClass/SetNodeSetReaderClass](#)*

Set default reader class.

`void SetSlotReaderClass(void *CSlotReaderBaseClass)`

`void SetNodePointReaderClass(void *CNodePointReaderBaseClass)`

`void SetNodeReaderClass(void *CNodeReaderBaseClass)`

`void SetNodeSetReaderClass(void *CNodeSetReaderBaseClass)`

*[GetSlotReaderClass/GetNodePointReaderClass/GetNodeReaderClass/GetNodeSetReaderClass](#)*

Get default reader class.

`void *GetSlotReaderClass()`

`void *GetNodePointReaderClass()`

`void *GetNodeReaderClass()`

`void *GetNodeSetReaderClass()`

*[GetSlotReader/GetSlotReaderEx](#)*

SlotReaderClass can be NULL(using the class register to nodeset via SetSlotReaderClass, or CSlotReaderBase), or a subclass of CSlotReaderBase.This class defines properties, which can be obtained by property name. You can extend the definition of attributes by defining subclasses and overloading the OnGetValue function

`void *GetSlotReader(void *SlotReaderClass,VS_CHAR *SourcePointKey)`

`void *GetSlotReaderEx(void *SlotReaderClass, void *CNodePoint,VS_CHAR *SlotID)`

*[GetNodePointReader](#)*

NodePointReaderClass can be NULL(using the class register to nodeset via SetNodePointReaderClass, or CNodePointReaderBase), or a subclass of CNodePointReaderBase.This class defines properties, which can be obtained by property name. You can extend the definition of attributes by defining subclasses and overloading the OnGetValue function

`void *GetNodePointReader(void *NodePointReaderClass, void *CNodePoint)`

*[GetNodeReader](#)*

NodeReaderClass can be NULL(using the class register to nodeset via SetNodeReaderClass, or CNodeReaderBase), or a subclass of CNodeReaderBase.This class defines properties, which can be obtained by property name. You can extend the definition of attributes by defining subclasses and overloading the OnGetValue function

`void *GetNodeReader(void *NodeReaderClass, void *CNode)`

*[GetReader](#)*

NodeSetReaderClass can be NULL(using the class register to nodeset via SetNodeSetReaderClass, or CNodeSetReaderBase), or a subclass of CNodeSetReaderBase.This class defines properties, which can be obtained by property name. You can extend the definition of attributes by defining subclasses and overloading the OnGetValue function

`void *GetReader(void *NodeSetReaderClass)`

NodeSet's function SetSlotReaderClass/SetNodePointReaderClass/SetNodeReaderClass/SetNodeSetReaderClass can be used to set default class.

<h1 align="center">CSlotReaderBase</h1>

*[OnGetValue](#)*

This function is overloaded in a subclass and returns attributes based on the name

`void *OnGetValue(void *CNodeSet,void *CNodePoint,VS_CHAR *SlotID,VS_CHAR *Name)`

#### a.Properties

* Set     : CNodeSetReader
* SlotID  : string 
* Point   : CNodePointReader 
* CNodeSet : CNodeSetBase
* CNodePoint : CNodePointBase

<h1 align="center">CNodePointReaderBase</h1>

*[OnGetValue](#)*

This function is overloaded in a subclass and returns attributes based on the name

`void *OnGetValue(void *CNodeSet, void *CNodePoint, VS_CHAR *Name)`

#### a.Properties

* Set      : CNodeSetReader
* Key      : string 
* Node     : CNodeReader
* CNodeSet : CNodeSetBase
* CNodePoint : CNodePointBase

<h1 align="center">CNodeReaderBase</h1>

*[OnGetValue](#)*

This function is overloaded in a subclass and returns attributes based on the name

`void *OnGetValue(void *CNodeSet, void *CNode, VS_CHAR *Name)`

#### a.Properties

* Key      : string 
* Set      : CNodeSetReader
* CNodeSet  : CNodeSetBase
* CNode    : CNodeBase

<h1 align="center">CNodeSetReaderBase</h1>

*[OnGetValue](#)*

This function is overloaded in a subclass and returns attributes based on the name

`void *OnGetValue(void *CNodeSet, VS_CHAR *Name)`

#### a.Properties

* CNodeSet  : CNodeSetBase










