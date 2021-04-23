import sys
import os

try:
  import cnode
  from cnode.node import *
  from cnode.pcnode import PCNodeManager as pcm
except Exception as exc:
  cnode_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../')
  sys.path.insert(0,cnode_path)
  import cnode
  from cnode.node import *
  from cnode.pcnode import PCNodeManager as pcm

Service = cnode.cleinit()

#创建根realm和nodeset
realm = Service.PCRealmBase()
nodeset = Service.CNodeSetBase('MySetClass')

pcm.Init(nodeset,realm)

import pchain
from pchain import pydata
from pchain import pyproc

@pyproc.DefineProc('TestProcClass1',(pydata.pfloat,pydata.pfloat),pydata.pbool)
def Execute(self,num1,num2) :
  Context = self.Context  #  first must save Context in local variable
  if num1.value() < num2.value() :
    return (0,1,pydata.pbool(True))
  return (0,1,pydata.pbool(False))

#----------------------------------------------------------------------
RunnerClass = Service.CNodeRunnerBase("MyRunner")
@RunnerClass._RegScriptProc_P('OnExecute')
def OnExecute(self,CNodeSet) :
  change = self.FetchChange(-1)
  print('Runner............',change)
  Frame = []
  for item in change :               #调用GetOutput可能导致其它对象状态变化，如果其它对象，在change中，则不应该再变化
      #CNodeSet.ExpandTarget(item)
      item.GetOutput()
      if item.IsActive() == True :
        Frame.append(item)
  self.SetFrame(-1,Frame)
  return True
#----------------------------------------------------------------------
#execute
val1 = pydata.pfloat(1.0)
val2 = pydata.pfloat(2.0)
nodeset.Reset()
node1 = pcm.ToNode(val1)
node2 = pcm.ToNode(val2)
vv1 = pcm.FromNode(node1)
vv2 = pcm.FromNode(node2)

val_str = pydata.pstr('Compare')
node_str = pcm.ToNode(val_str)

node_function = pcm.ToNode(TestProcClass1)

#创建关系，字符串与函数节点，创建时，不关系函数节点input point的Key，由平台自动分配
with RelationControl(nodeset) as rc :
  rc._(node_str,node_function)

node1.SetOutput(1.0)
node2.SetOutput(1.0)
node_str.SetOutput(1.0)

nodeset.ActiveBatchNode([node1,node2,node_str])

runner = nodeset.CreateRunner(RunnerClass)
Result = nodeset.Execute()
print('active node is :  ',str(Result))

Result = nodeset.Execute()
print('active node is :  ',str(Result))

#Result[0].Approval(1.0)

cnode.cleterm()
