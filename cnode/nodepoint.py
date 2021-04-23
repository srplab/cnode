import cnode
Service = cnode.cleinit()

#define input point class
WhenAnyPointClass = Service.CNodePointBase('WhenAnyPointClass')
@WhenAnyPointClass._RegScriptProc_P('OnExecute')
def OnExecute(self,CNodeSet,CNode) :
  node_active_flag = self.GetSourceActiveFlag()
  for flag in node_active_flag :
    if flag == True :
      return 1.0
  return 0.0

#define input point class
WhenAllPointClass = Service.CNodePointBase('WhenAllPointClass')
@WhenAllPointClass._RegScriptProc_P('OnExecute')
def OnExecute(self,CNodeSet,CNode) :
  node_active_flag = self.GetSourceActiveFlag()
  for flag in node_active_flag :
    if flag == False :
      return 0.0
  return 1.0
  
#define node output point class
GeneralOutputClass = Service.CNodePointBase('GeneralOutputClass')
@GeneralOutputClass._RegScriptProc_P('OnExecute')
def OnExecute(self,CNodeSet,CNode) :
  node_active_flag = self.GetSourceActiveFlag()
  node_negativeflag = self.GetSourceNegativeFlag()
  
  active = False
  for i in range(0,len(node_active_flag)) :
    if node_active_flag[i] == True and node_negativeflag[i] == False :
      active = True  
      break
  
  if active == True :
    #conflict ?
    for i in range(0,len(node_active_flag)) :
      if node_active_flag[i] == True and node_negativeflag[i] == True :
        #conflict, fire the callback
        nodeset = self.GetNodeSet()
        nodeset.ExecuteIssue(self,cnode.EXECUTE_CONFLICT)
        break
  
  if active == True :
    return 1.0         
  return 0.0

#define proc input define class
ProcInputDefineClass = Service.CNodePointBase('ProcInputDefineClass')
@ProcInputDefineClass._RegScriptProc_P('OnExecute')
def OnExecute(self,CNodeSet,CNode) :
  pass