export class SchedH6Model {
    cmte_id: string;
    report_id: number;
    transaction_type_identifier: string;
    transaction_id: string;
    back_ref_transaction_id: string;
    activity_event_identifier: string;
    activity_event_type: string;
    expenditure_date:string;
    expenditure_purpose:string;
    fed_share_amount: number;
    non_fed_share_amount: number;
    levin_share: number;
    memo_code: string;
    first_name: string;
    last_name: string;
    entity_name: string;
    entity_type: string;
    arrow_dir: string;
    aggregation_ind: string;
    child: SchedH6Model[] = [];
    constructor(schedH6: any) {
        this.cmte_id = schedH6.cmte_id ? schedH6.cmte_id : '';
        this.report_id = schedH6.report_id ? schedH6.report_id : '';
        this.transaction_type_identifier = schedH6.transaction_type_identifier ? schedH6.transaction_type_identifier : '';
        this.transaction_id = schedH6.transaction_id ? schedH6.transaction_id : '';
        this.back_ref_transaction_id = schedH6.back_ref_transaction_id ? schedH6.back_ref_transaction_id : '';
        this.activity_event_identifier = schedH6.activity_event_identifier ? schedH6.activity_event_identifier : '';
        this.activity_event_type = schedH6.activity_event_type ? schedH6.activity_event_type : '';
        this.expenditure_date = schedH6.expenditure_date ? schedH6.expenditure_date : '';
        this.expenditure_purpose = schedH6.expenditure_purpose ? schedH6.expenditure_purpose : '';
        this.fed_share_amount = schedH6.fed_share_amount ? schedH6.fed_share_amount : '';
        this.levin_share = schedH6.levin_share ? schedH6.levin_share : '';
        this.non_fed_share_amount = schedH6.non_fed_share_amount ? schedH6.non_fed_share_amount : '';
        this.memo_code = schedH6.memo_code ? schedH6.memo_code : '';
        this.first_name = schedH6.first_name ? schedH6.first_name : '';
        this.last_name = schedH6.last_name ? schedH6.last_name : '';
        this.entity_name = schedH6.entity_name ? schedH6.entity_name : '';
        this.entity_type = schedH6.entity_type ? schedH6.entity_type : '';
        this.arrow_dir = schedH6.arrow_dir ? schedH6.arrow_dir : '';
        this.child = schedH6.child;
        this.aggregation_ind = schedH6.aggregation_ind;
    }
}
