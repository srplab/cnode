<h1 align="center">CNodePatternBase</h1>

CNodePattern is used to process the NodePoint's Source Node, which can be called in the OnExecute callback function of CNodePoint. Used to judge the rationality of the current Source Node, or to obtain a new Source Node.

**[Only nodepoint which dynamic flag is false can have pattern](#)**

**[CNodePattern objects are attached to a input point of Node, but not only needs to handle the relationship between the source node of the input point, but also needs to record and handle the relationship across the input points](#)**

Define CNodePattern Type and Create Instance
------

**1. define CNodePattern type**

```python
MyPatternClass = Service.CNodePatternBase('MyPatternClass')
@MyPatternClass._RegScriptProc_P('OnExecute')
def OnExecute(self,CNodeSet,CNode,CNodePoint) :
  source = self.GetSource()
  ...
  return False
```

**2. Create instance of CNodePattern**

Do not create an instance of CNodePattern directly, but using CNodePoint's CreatePattern

Functions supported by CNodePattern
------

*[SetLabel](#)*

`void SetLabel(VS_CHAR *Label)`

*[GetLabel](#)*

`VS_CHAR *GetLabel()`

*[GetNodePoint](#)*

Get the NodePoint to which the pattern belongs

`void *GetNodePoint()`

*[SetParameter](#)*

Set the Parameter. The input value maybe bool, int, double, parapkg or string. If Value is NULL, then the parameter will be removed

`VS_BOOL SetParameter(VS_CHAR *Name, void *Value)`

*[GetParameter/Parameter](#)*

Get the Parameter. The return value maybe bool, int, double, parapkg or string

`void *GetParameter(VS_CHAR *Name)`

`VS_PARAPKGPTR Parameter()`

*[GetParameterKey](#)*

`VS_PARAPKGPTR GetParameterKey()`

*[OnExecute](#)*

`VS_BOOL OnExecute(void *CNodeSet,void *CNode,void *CNodePoint)`

This callback function is called when the Output point of node is to be evaluated. And the input node has been evaluated.

If the function returns false, the pattern will be removed from the point.

*[OnExtract](#)*

Extract relationships among input nodes. Which is called when the nodepoint's function Approval is called.

`VS_BOOL OnExtract(void *CNodeSet,void *CNode,void *CNodePoint)`

If the function returns false, the pattern will be removed from the point.

*[OnMerge](#)*

Called when saving, merge the parameters of the source object list into this object 

`VS_BOOL OnMerge(void *CNodeSet, void *CNode, void *CNodePoint, VS_PARAPKGPTR SourcePatternList)`
