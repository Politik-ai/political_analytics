from init_db import *



def bill_final_status(bill):
    if not bill.status:
        return "Unknown"
    status_dict = {}
    status_dict['INTRODUCED'] = {'s':None, 'hr':None}
    status_dict['REFERRED'] = {'s':None, 'hr':None}
    status_dict['PASS_OVER:HOUSE'] = {'s':False, 'hr':True}
    status_dict['PASS_OVER:SENATE'] = {'s':True, 'hr':None}
    status_dict['PASSED:BILL'] = {'s':True, 'hr':True}
    status_dict['PASSED:CONCURRENTRES'] = {'s':True, 'hr':True}
    status_dict['FAILED:SECOND:HOUSE'] = {'s':True, 'hr':False}
    status_dict['FAILED:SECOND:SENATE'] = {'s':False, 'hr':True}
    status_dict['ENACTED:SIGNED'] = {'s':True, 'hr':True}
    status_dict['PROV_KILL:VETO'] = {'s':True, 'hr':True}
    status_dict['VETOED:POCKET'] = {'s':True, 'hr':True}

    #Simple Resolutions only matter for one body 
    status_dict['PASSED:SIMPLERES'] = {'s':None, 'hr':None}
    status_dict['PASSED:SIMPLERES'][bill.originating_body] = True

    status_dict['PASSED:CONSTAMEND'] = {'s':True, 'hr':True}
    status_dict['PASSED:CONCURRENTRES'] = {'s':True, 'hr':True}

    # NOTE: HOW SHOULD Passed back be considered in stats?
    # If considering the past only, would be fail for other house if most current bill_status is considered?
    # But an earlier version did pass, so that should be considered too?
    status_dict['PASS_BACK:HOUSE'] = {'s':False, 'hr':True}
    status_dict['PASS_BACK:SENATE'] = {'s':True, 'hr':False}
    
    #Same issue, not sure how to consider this with limited information.
    status_dict['PROV_KILL:PINGPONGFAIL'] = {'s':None, 'hr':None}


    #Considering veto situations? How to do? For now just act as though it passed hr/s
    status_dict['VETOED:OVERRIDE_FAIL_ORIGINATING:HOUSE'] = {'s':True, 'hr':True}
    status_dict['VETOED:POCKET'] = {'s':True, 'hr':True}
    status_dict['VETOED:OVERRIDE_FAIL_ORIGINATING:SENATE'] = {'s':True, 'hr':True}
    status_dict['VETOED:OVERRIDE_PASS_OVER:HOUSE'] = {'s':True, 'hr':True}
    status_dict['VETOED:OVERRIDE_PASS_OVER:SENATE'] = {'s':True, 'hr':True}
    status_dict['VETOED:OVERRIDE_FAIL_SECOND:HOUSE'] = {'s':True, 'hr':True}
    status_dict['VETOED:OVERRIDE_FAIL_SECOND:SENATE'] = {'s':True, 'hr':True}
    status_dict['ENACTED:VETO_OVERRIDE'] = {'s':True, 'hr':True}
    status_dict['ENACTED:TENDAYRULE'] = {'s':True, 'hr':True}



    final_status = status_dict.get(bill.status, None)
    if not final_status:
        print(f'Could not find status type: {bill.status}')
    return final_status

