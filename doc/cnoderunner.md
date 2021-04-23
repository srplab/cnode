<h1 align="center">CNodeRunner</h1>

CNodeRunner is used to run according to the relationship between nodes, activate related nodes, and run action nodes.

**[CNodeRunner objects are attached to a NodeSet object](#)**

Create CNodeRunner Instance
------

**1. Create instance of CNodeRunner**

Do not create an instance of CNodeRunner directly, but using CNodeSet's CreateRunner

```
runner = nodeset.CreateRunner()
```  

The current runner object can be obtained via CNodeSet's function CurrentRunner.

Functions supported by CNodeRunner
------

*[GetNodeSet](#)*

Get the NodeSet object

`void *GetNodeSet()`

*[CreateInputPoint](#)*

If the same key already exists, it fails

`void *CreateInputPoint(void *CNode, void *CNodePointClass, VS_CHAR *InputPointKey, VS_INT32 MaxSlotNumber,VS_BOOL IsNegative, VS_BOOL IsNotCondition)`

MaxSlotNumber = 0 means no limit

**[If IsNegative is true, the node should be inactive when the input point is activated](#)**

**[If IsNotCondition is true, the input node point's ConditionFlag will be set to false, then when calculating the output, it should not be taken into account, and the intermediate node of Node should not be connected to it.](#)**

**[The input point created in this way is generally considered to be an assumption, and its DynamicFlag is always true.](#)**

**[InputPointKey maybe NULL or empty string](#)**

*[CanAsTargetNode](#)*

If MustHasEmptySlot true, the TargetNode must has empty target slot.

`VS_BOOL CanAsTargetNode(void *CNode, void *TargetNode, VS_CHAR *TargetNodePointKey, VS_BOOL MustHasEmptySlot)`

*[IsTargetNodeConnect](#)*

Node is already conected to this Node as target node point

`VS_BOOL IsTargetNodeConnect(void *CNode, void *TargetNode, VS_CHAR *TargetNodePointKey, VS_CHAR *SlotID)`

SlotID maybe NULL or empty string.

*[ConnectTargetNode](#)*

Connect this Node to the input point of the target Node. 

**[TargetNode must have an empty slot or have not established a connection with a node with the same Key](#)**

**[SlotID maybe NULL or empty string. In this case,if the NodePoint is already connected to other nodes and has no empty slots, this function will disconnect the current connection for new.To avoid this situation, you can use the DisConnect function to release the slot first.](#)**

If SlotID does not exist, new source point will be added for input point of the target Node.

`VS_BOOL ConnectTargetNode(void *CNode, void *TargetNode, VS_CHAR *TargetNodePointKey, VS_CHAR *SlotID)`

*[DisConnectTargetNode](#)*

Delete the connection to the target node

`VS_BOOL DisConnectTargetNode(void *CNode, void *TargetNode, VS_CHAR *TargetNodePointKey, VS_CHAR *SlotID)`

SlotID may be NULL or empty string.

*[CanAsSourceNode](#)*

`VS_BOOL CanAsSourceNode(void *CNode, VS_CHAR *NodePointKey,void *SourceNode)`

*[IsSourceNodeConnect](#)*

SourceNode is already conected to this Node or not

`VS_BOOL IsSourceNodeConnect(void *CNode, VS_CHAR *NodePointKey, VS_CHAR *SlotID, void *SourceNode)`

SlotID maybe NULL or empty string.

*[ConnectSourceNode](#)*

Connect this SourceNode to the input point of the Node. 

**[SlotID maybe NULL or empty string, in this case, empty slot will be used. If input point of the Node is already connected to other nodes and has no empty slots, this function will create a new slot for input point of the target Node. ](#)**

If SlotID does not exist, new source point will be added for input point of the target Node.

`VS_BOOL ConnectSourceNode(void *CNode, VS_CHAR *NodePointKey, VS_CHAR *SlotID, void *SourceNode)`

*[DisConnectSourceNode](#)*

Delete the connection to the source node

`VS_BOOL DisConnectSourceNode(void *CNode, VS_CHAR *NodePointKey, VS_CHAR *SlotID, void *SourceNode)`

SlotID may be NULL or empty string.

*[SetParameter](#)*

Set the Parameter. The input value maybe bool, int, double, parapkg or string. If Value is NULL, then the parameter will be removed

`VS_BOOL SetParameter(VS_CHAR *Name, void *Value)`

*[GetParameter/Parameter](#)*

Get the Parameter. The return value maybe bool, int, double, parapkg or string

`void *GetParameter(VS_CHAR *Name)`

`VS_PARAPKGPTR Parameter()`

*[GetParameterKey](#)*

`VS_PARAPKGPTR GetParameterKey()`

*[InitDeactive](#)*

The new node is forced to be inactive regardless of the output value. 

`VS_BOOL InitDeactive()`

*[OnInit](#)*

In this function, you can get the currently activated node and set the node that the initial frame focuses on 

`VS_BOOL OnInit(void *CNodeSet)`

*[OnExecute](#)*

This function is called by NodeSet's Execute(). In this function, use runner's GetChange to get the changed node.

`VS_BOOL OnExecute(void *CNodeSet)`

*[FrameNumber](#)*

Return current frame number.

`VS_INT64 FrameNumber()`

*[SetFrame](#)*

Set the node list of a frame. If FrameNumber == -1, means, is current FrameNumber + 1. The function will set node to active.

`VS_BOOL SetFrame(VS_INT64 FrameNumber, VS_PARAPKGPTR CNodeList)`

*[GetFrame](#)*

Get node list of a frame

`VS_PARAPKGPTR GetFrame(VS_INT64 FrameNumber)`

*[NodeFrame](#)*

Get the frame number of Node, if it does not exist, return -1 

`VS_INT64 NodeFrame(struct StructOfCNodeBase *CNodeBase)`

*[FirstFrame](#)*

Get the smallest frame number. If the node is not in any previous frame, return -1 

`VS_INT64 FirstFrame(VS_PARAPKGPTR CNodeList)`

*[LastFrame](#)*

Get the biggest frame number. If the node is not in any previous frame, return -1 

`VS_INT64 LastFrame(VS_PARAPKGPTR CNodeList)`

*[FrameList](#)*

Get the frame number list of each node of CNodeList belongs.

`VS_PARAPKGPTR FrameList(VS_PARAPKGPTR CNodeList)`

*[FetchChange](#)*

Get the changed nodes in the runner belong to a frame, and the returned nodes are arranged in order. This function will remove the changed nodes returned from change record.

If FrameNumber == -1, return the changed nodes not in any frame.

This function should be called in the OnExecute callback function 

`VS_PARAPKGPTR FetchChange(VS_INT64 FrameNumber)`

*[SetChange](#)*

Insert node to change record.

`void SetChange(VS_PARAPKGPTR CNodeList)`

*[ClearChange](#)*

`void ClearChange()`

*[Reset](#)*

Clear frame euqal or higher than FrameNumber

`void Reset(VS_INT64 FrameNumber)`

*[HasIfSource](#)*

There is a node activated by calling the function of the runner, or there is a connection established by calling the function of the runner 

`VS_BOOL HasIfSource(void *CNode)`














