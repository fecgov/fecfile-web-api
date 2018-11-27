export interface IAccount{
    committeeid: string;
    committeename: string;
    street1: string;
    street2: string;
    city: string;
    state: string;
    zipcod: string;
    treasurerprefix: string;
    treasurerfirstname: string;
    treasurermiddlename: string;
    treasurerlastname: string;
    treasurersuffix: string;
    email_on_file: string;
    created_at: string;
    treasurerstreet1: string;
    treasurerstreet2: string;
    treasurercity: string;
    treasurerstate: string;
    treasurerzipcode: string;
}
 export class Account implements IAccount{
    public committeeid: string;
    public committeename: string;
    public street1: string;
    public street2: string;
    public city: string;
    public state: string;
    public zipcod: string;
    public treasurerprefix: string;
    public treasurerfirstname: string;
    public treasurermiddlename: string;
    public treasurerlastname: string;
    public treasurersuffix: string;
    public email_on_file: string;
    public created_at: string;
    public treasurerstreet1: string;
    public treasurerstreet2: string;
    public treasurercity: string;
    public treasurerstate: string;
    public treasurerzipcode: string;     
 }