export class SchedLModel {
    cmte_id: string;
    report_id: number;
    transaction_type_identifier: string;
    tran_desc: string;
    transaction_id: string;
    back_ref_transaction_id: string;
    levin_account_id: string;
    levin_account_name: string;
    contribution_date: string;
    expenditure_date: string;
    date: any;
    amount: any;
    aggregate: any;
    contribution_amount: string;
    expenditure_amount: string;
    memo_code: string;
    first_name: string;
    last_name: string;
    entity_name: string;
    entity_type: string;
    arrow_dir: string;
    constructor(schedL: any) {
        this.cmte_id = schedL.cmte_id ? schedL.cmte_id : '';
        this.report_id = schedL.report_id ? schedL.report_id : '';
        this.transaction_type_identifier = schedL.transaction_type_identifier ? schedL.transaction_type_identifier : '';
        this.tran_desc = schedL.tran_desc ? schedL.tran_desc : '';
        this.transaction_id = schedL.transaction_id ? schedL.transaction_id : '';
        this.back_ref_transaction_id = schedL.back_ref_transaction_id ? schedL.back_ref_transaction_id : '';
        this.levin_account_id = schedL.levin_account_id ? schedL.levin_account_id : '';
        this.levin_account_name = schedL.levin_account_name ? schedL.levin_account_name : '';
        this.contribution_date = schedL.contribution_date ? schedL.contribution_date : '';
        this.expenditure_date = schedL.expenditure_date ? schedL.expenditure_date : '';
        this.date = schedL.date ? schedL.date : null;
        this.contribution_amount = schedL.contribution_amount ? schedL.contribution_amount : '';
        this.expenditure_amount = schedL.expenditure_amount ? schedL.expenditure_amount : '';
        this.amount = schedL.amount ? schedL.amount : '';
        this.aggregate = schedL.aggregate ? schedL.aggregate : '';
        this.memo_code = schedL.memo_code ? schedL.memo_code : '';
        this.first_name = schedL.first_name ? schedL.first_name : '';
        this.last_name = schedL.last_name ? schedL.last_name : '';
        this.entity_name = schedL.entity_name ? schedL.entity_name : '';
        this.entity_type = schedL.entity_type ? schedL.entity_type : '';
        this.arrow_dir = schedL.arrow_dir ? schedL.arrow_dir : '';
    }
}