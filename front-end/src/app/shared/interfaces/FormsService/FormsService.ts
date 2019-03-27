export interface form99 {
  id: string,
  committeeid: string,
  committeename: string,
  street1: string,
  street2: string,
  city: string,
  state: string,
  zipcode: string,
  treasurerprefix: string,
  treasurerfirstname: string,
  reason: string,
  text: string,
  treasurermiddlename: string,
  treasurerlastname: string,
  treasurersuffix: string,
  signee: string,
  email_on_file: string,
  email_on_file_1: string,
  additional_email_1: string,
  additional_email_2: string,
  created_at: string,
  is_submitted: boolean,
  filename:string,
  form_type:string,
  file:any,
  org_filename?:string,
  org_fileurl?:string,
  printpriview_filename?:string,
  printpriview_fileurl?:string
 }

export interface Icommittee_forms {
  category?: string,
  form_type?: string,
  form_description?: string,
  form_info?: string,
  due_date?: string,
  cmte_id?:string,
  form_pdf_url?:string,
  form_type_mini?: string,
}

export interface form3x_data {
  cashOnHand?: any,
  steps?: any,
  transactionCategories?: string,
  transactionSearchField?: string
}

export interface form3x {
  category?: string,
  report_id?: string,
  cmte_id?: string,
  cmte_nm?: string,
  cmte_addr_chg_flag?: string,
  cmte_street_1?: string,
  cmte_street_2?: string,
  cmte_city?: string,
  cmte_state?: string,
  cmte_zip?: string,
  report_type?: string,
  election_code?: string,
  date_of_election?: string,
  state_of_election?: string,
  cvg_start_dt?: string,
  cvg_end_dt?: string,
  qual_cmte_flag?: string,
  treasurer_last_name?: string,
  treasurer_first_name?: string,
  treasurer_middle_name?: string,
  treasurer_prefix?: string,
  treasurer_suffix?: string,
  date_signed?: string,
  coh_bop?: string,
  ttl_receipts_sum_page_per?: string,
  subttl_sum_page_per?: string,
  ttl_disb_sum_page_per?: string,
  coh_cop?: string,
  debts_owed_to_cmte?: string,
  debts_owed_by_cmte?: string,
  indv_item_contb_per?: string,
  indv_unitem_contb_per?: string,
  ttl_indv_contb?: string,
  pol_pty_cmte_contb_per_i?: string,
  other_pol_cmte_contb_per_i?: string,
  ttl_contb_col_ttl_per?: string,
  tranf_from_affiliated_pty_per?: string,
  all_loans_received_per?: string,
  loan_repymts_received_per?: string,
  offsets_to_op_exp_per_i?: string,
  fed_cand_contb_ref_per?: string,
  other_fed_receipts_per?: string,
  tranf_from_nonfed_acct_per?: string,
  tranf_from_nonfed_levin_per?: string,
  ttl_nonfed_tranf_per?: string,
  ttl_receipts_per?: string,
  ttl_fed_receipts_per?: string,
  shared_fed_op_exp_per?: string,
  shared_nonfed_op_exp_per?: string,
  other_fed_op_exp_per?: string,
  ttl_op_exp_per?: string,
  tranf_to_affliliated_cmte_per?: string,
  fed_cand_cmte_contb_per?: string,
  indt_exp_per?: string,
  coord_exp_by_pty_cmte_per?: string,
  loan_repymts_made_per?: string,
  loans_made_per?: string,
  indv_contb_ref_per?: string,
  pol_pty_cmte_contb_per_ii?: string,
  other_pol_cmte_contb_per_ii?: string,
  ttl_contb_ref_per_i?: string,
  other_disb_per?: string,
  shared_fed_actvy_fed_shr_per?: string,
  shared_fed_actvy_nonfed_per?: string,
  non_alloc_fed_elect_actvy_per?: string,
  ttl_fed_elect_actvy_per?: string,
  ttl_disb_per?: string,
  ttl_fed_disb_per?: string,
  ttl_contb_per?: string,
  ttl_contb_ref_per_ii?: string,
  net_contb_per?: string,
  ttl_fed_op_exp_per?: string,
  offsets_to_op_exp_per_ii?: string,
  net_op_exp_per?: string,
  coh_begin_calendar_yr?: string,
  calendar_yr?: string,
  ttl_receipts_sum_page_ytd?: string,
  subttl_sum_ytd?: string,
  ttl_disb_sum_page_ytd?: string,
  coh_coy?: string,
  indv_item_contb_ytd?: string,
  indv_unitem_contb_ytd?: string,
  ttl_indv_contb_ytd?: string,
  pol_pty_cmte_contb_ytd_i?: string,
  other_pol_cmte_contb_ytd_i?: string,
  ttl_contb_col_ttl_ytd?: string,
  tranf_from_affiliated_pty_ytd?: string,
  all_loans_received_ytd?: string,
  loan_repymts_received_ytd?: string,
  offsets_to_op_exp_ytd_i?: string,
  fed_cand_cmte_contb_ytd?: string,
  other_fed_receipts_ytd?: string,
  tranf_from_nonfed_acct_ytd?: string,
  tranf_from_nonfed_levin_ytd?: string,
  ttl_nonfed_tranf_ytd?: string,
  ttl_receipts_ytd?: string,
  ttl_fed_receipts_ytd?: string,
  shared_fed_op_exp_ytd?: string,
  shared_nonfed_op_exp_ytd?: string,
  other_fed_op_exp_ytd?: string,
  ttl_op_exp_ytd?: string,
  tranf_to_affilitated_cmte_ytd?: string,
  fed_cand_cmte_contb_ref_ytd?: string,
  indt_exp_ytd?: string,
  coord_exp_by_pty_cmte_ytd?: string,
  loan_repymts_made_ytd?: string,
  loans_made_ytd?: string,
  indv_contb_ref_ytd?: string,
  pol_pty_cmte_contb_ytd_ii?: string,
  other_pol_cmte_contb_ytd_ii?: string,
  ttl_contb_ref_ytd_i?: string,
  other_disb_ytd?: string,
  shared_fed_actvy_fed_shr_ytd?: string,
  shared_fed_actvy_nonfed_ytd?: string,
  non_alloc_fed_elect_actvy_ytd?: string,
  ttl_fed_elect_actvy_ytd?: string,
  ttl_disb_ytd?: string,
  ttl_fed_disb_ytd?: string,
  ttl_contb_ytd?: string,
  ttl_contb_ref_ytd_ii?: string,
  net_contb_ytd?: string,
  ttl_fed_op_exp_ytd?: string,
  offsets_to_op_exp_ytd_ii?: string,
  net_op_exp_ytd?: string,
  create_date?: string,
  last_update_date?: string
  }

export interface Icommittee_form3x_reporttype {
  report_type?: string,
  rpt_type_desc?: string,
  regular_special_report_ind?: string,
  rpt_type_info?: string,
  cvg_start_date?: string,
  cvg_end_date?: string,
  due_date?:string
}

export interface Ielection_state {
  state?: string,
  dates?: string[]
}

export interface Ielection_state_date {
  election_date?: string,
  cvg_start_date?: string,
  cvg_end_date?: string,
  due_date?: string
}

export interface f3xTransactionTypes {
  formFields?: Array<any>,
  states?: Array<any>,
  transactionCategories?: Array<any>
}
  export interface selectedElectionDate{
    election_date?: string,
    cvg_start_date?: string,
    cvg_end_date?: string,
    due_date?: string
  }

  export interface form3XReport {
    cmteId?:string;
    reportId?: string,
    formType?:string;
    amend_Indicator?:string;
    reportType?: string,
    regularSpecialReportInd?: string,
    electionCode?: string,
    stateOfElection?:string,
    electionDate?:string,
    cvgStartDate?: string,
    cvgEndDate?:string,
    dueDate?:string,
    coh_bop?:string
  }

  export interface selectedElectionState{
    state?: string,
    state_description?: string,
    dates?: Array<selectedElectionDate>
  }

  export interface selectedReportType
  {
    default_disp_ind?: string,
    election_state?: Array<selectedElectionState>,
    regular_special_report_ind?: string,
    report_type?: string ,
    report_type_desciption?: string,
    report_type_info?: string,
  }

  export interface form99PrintPreviewResponse{
    message?:string,
    results?:pdfResonse,
    success?:string
  }

  export interface pdfResonse{
    pdf_url?:string,
   }

  export interface IReport{
    report_id: string,
    form_type: string,
    amend_ind: string,
    amend_number: number,
    cmte_id: string,
    report_type: string,
    report_type_desc: string,
    cvg_start_date: string,
    cvg_end_date: string,
    due_date: string,
    superceded_report_id: string,
    previous_report_id: string,
    status: string,
    filed_date: string,
    fec_id: string,
    fec_accepted_date: string,
    fec_status: string,
    most_recent_flag: string,
    delete_ind: string,
    create_date: string,
    last_update_date: string
   }
  
   

 export class reportModel {
  id: string;
  report_id: string;
  form_type: string;
  amend_ind: string;
  amend_number: number;
  cmte_id: string;
  report_type: string;
  report_type_desc: string;
  cvg_start_date: string;
  cvg_end_date: string;
  due_date: string;
  superceded_report_id: string;
  previous_report_id: string;
  status: string;
  filed_date: string;
  fec_id: string;
  fec_accepted_date: string;
  fec_status: string;
  most_recent_flag: string;
  delete_ind: string;
  create_date: string;
  last_update_date: string;
  viewtype: string;

  constructor(report: any) {
    this.id = report.id ? report.id : '';
    this.report_id = report.report_id ? report.report_id: '';
    this.form_type = report.form_type ? report.form_type : '';
    this.amend_ind = report.amend_ind ? report.amend_ind : '';
    this.amend_number = report.amend_number ? report.amend_amend_numberind : 0;
    this.cmte_id = report.cmte_id ? report.cmte_id : '';
    this.report_type = report.report_type ? report.report_type : '';
    this.report_type_desc = report.report_type_desc ? report.report_type_desc : '';
    this.cvg_start_date = report.cvg_start_date ? report.cvg_start_date : null;
    this.cvg_end_date = report.cvg_end_date ? report.cvg_end_date : null;
    this.due_date = report.due_date ? report.due_date : null;
    this.superceded_report_id = report.superceded_report_id ? report.superceded_report_id : null;
    this.previous_report_id = report.previous_report_id ? report.previous_report_id : null;
    this.status = report.status ? report.status : '';
    this.filed_date = report.filed_date ? report.filed_date : '';
    this.fec_accepted_date = report.fec_accepted_date ? report.fec_accepted_date : '';
    this.most_recent_flag = report.most_recent_flag ? report.most_recent_flag : '';
    this.delete_ind = report.delete_ind ? report.delete_ind : '';
    this.fec_status = report.fec_status ? report.fec_status : '';
    this.create_date = report.create_date ? report.create_date : '';
    this.last_update_date = report.last_update_date ? report.last_update_date : '';
    this.viewtype = report.viewtype ? report.viewtype : '';
    //this.selected = report.selected;
  }
 }
 
