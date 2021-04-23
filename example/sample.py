import sys
import os
try:
  import cnode
except Exception as exc:
  cnode_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../')
  sys.path.insert(0,cnode_path)
  import cnode  

Service = cnode.cleinit()

#define node point class
PointClass = Service.CNodePointBase('PointClass')
@PointClass._RegScriptProc_P('OnExecute')
def OnExecute(self,CNodeSet,CNode) :
  node_output = self.GetSourceOutput()
  if len([t for t in node_output if t >= 0.5]) :
    return 1.0
  return 0.0
  
@PointClass._RegScriptProc_P('OnCreatePattern')
def OnCreatePattern(self) :
  print('OnCreatePattern......................')
  return 
  
@PointClass._RegScriptProc_P('OnApproval')
def OnApproval(self,CNodeSet,CNode,TargetValue) :
  print('OnApproval......................',CNodeSet,CNode,TargetValue)
  return   
     
#create set
MySetClass = Service.CNodeSetBase('MySetClass')
set = MySetClass()

#define node
set.DefineNode('node1', '',0,PointClass)
set.DefineNode('node2', '',0,PointClass)  

#create node
node1 = set.CreateNode('node1',None)
node2 = set.CreateNode('node2',None)

#create relation
node2.CreateInputPoint(PointClass,'in1',0,False, False,False)

#set.CreateBatchRelation((node1,),node2,'in1')
set.CreateRelation(node1,node2,'in1')

print(set.GetRelationID(node1,node2,'in1'))

#----------------------------------------------------------------------
RunnerClass = Service.CNodeRunnerBase("MyRunner")
#----------------------------------------------------------------------
#create Event
EventClass = Service.CNodeEventBase("MyEvent")
@EventClass._RegScriptProc_P('OnInit')
def OnInit(self,CNodeSet) :
  print(self,'OnInit')
  print(cnode.EVENT_BEFORETURN)
  return cnode.EVENT_BEFORETURN

@EventClass._RegScriptProc_P('OnExecute')
def OnExecute(self,CNodeSet) :
  print(self,'OnExecute')
  return True
  
set.CreateEvent(EventClass)

#----------------------------------------------------------------------  
#execute
set.Reset(False)

node1.SetOutput(1.0)
set.ActiveNode(node1)
set.CreateRunner(RunnerClass)
Result = set.Execute()
print('active node is :  ',str(Result))

Result[0][1][0].ExpectOutput(1.0)

cnode.cleterm()
