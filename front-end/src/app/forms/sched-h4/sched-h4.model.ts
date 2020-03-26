export class SchedH4Model {
    cmte_id: string;
    report_id: number;
    transaction_type_identifier: string;
    transaction_id: string;
    back_ref_transaction_id: string;
    activity_event_identifier: string;
    activity_event_type: string;
    expenditure_date:string;
    fed_share_amount: number;
    non_fed_share_amount: number;
    memo_code: string;
    first_name: string;
    last_name: string;
    entity_name: string;
    entity_type: string;
    arrow_dir: string;
    aggregation_ind: string;
    child: SchedH4Model[] = [];
    constructor(schedH4: any) {
        this.cmte_id = schedH4.cmte_id ? schedH4.cmte_id : '';
        this.report_id = schedH4.report_id ? schedH4.report_id : '';
        this.transaction_type_identifier = schedH4.transaction_type_identifier ? schedH4.transaction_type_identifier : '';
        this.transaction_id = schedH4.transaction_id ? schedH4.transaction_id : '';
        this.back_ref_transaction_id = schedH4.back_ref_transaction_id ? schedH4.back_ref_transaction_id : '';
        this.activity_event_identifier = schedH4.activity_event_identifier ? schedH4.activity_event_identifier : '';
        this.activity_event_type = schedH4.activity_event_type ? schedH4.activity_event_type : '';
        this.expenditure_date = schedH4.expenditure_date ? schedH4.expenditure_date : '';
        this.fed_share_amount = schedH4.fed_share_amount ? schedH4.fed_share_amount : '';
        this.non_fed_share_amount = schedH4.non_fed_share_amount ? schedH4.non_fed_share_amount : '';
        this.memo_code = schedH4.memo_code ? schedH4.memo_code : '';
        this.first_name = schedH4.first_name ? schedH4.first_name : '';
        this.last_name = schedH4.last_name ? schedH4.last_name : '';
        this.entity_name = schedH4.entity_name ? schedH4.entity_name : '';
        this.entity_type = schedH4.entity_type ? schedH4.entity_type : '';
        this.arrow_dir = schedH4.arrow_dir ? schedH4.arrow_dir : '';
        this.child = schedH4.child;
    }
}
