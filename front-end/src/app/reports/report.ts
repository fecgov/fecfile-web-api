export interface IReport{
    id: string;
    committeeid: string;
    committeename: string;
    street1: string;
    street2: string;
    city: string;
    state: string;
    zipcode: string;
    treasurerprefix: string;
    treasurerfirstname: string;
    text: string;
    reason: string;
    treasurermiddlename: string;
    treasurerlastname: string;  
    treasurersufix: string;
    file: string;
    created_at: string
    is_submitted: boolean;
    signee: string;
    email_on_file: string;
    additional_email_1: string;
    additional_email_2: string;
    form_type: string;
    coverage_start_date: string;
    coverage_end_date: string;
}
 export class Report implements IReport{
    public id: string;
    public committeeid: string;
    public committeename: string;
    public street1: string;
    public street2: string;
    public city: string;
    public state: string;
    public zipcode: string;
    public treasurerprefix: string;
    public treasurerfirstname: string;
    public text: string;
    public reason: string;
    public treasurermiddlename: string;
    public treasurerlastname: string;  
    public treasurersufix: string;
    public file: string;
    public created_at: string
    public is_submitted: boolean;
    public signee: string;
    public email_on_file: string;
    public additional_email_1: string;
    public additional_email_2: string;
    public form_type: string;
    public coverage_start_date: string;
    public coverage_end_date: string;     
 }