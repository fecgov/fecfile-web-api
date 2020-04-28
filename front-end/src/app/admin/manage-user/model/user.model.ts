export class UserModel {
    firstName: string;
    lastName: string;
    email: string;
    role: string;
    status: boolean;
    id: number;
    contact: string;
    isActive: boolean;

    constructor(user: any) {
        this.firstName = user.first_name ? user.first_name : '';
        this.lastName = user.last_name ? user.last_name : '';
        this.email = user.email ? user.email : '';
        this.role = user.role ? user.role : '';
        this.status = user.is_active ? true : false;
        this.id = user.id ? user.id : 0;
        this.contact = user.contact ? user.contact : '';
        this.isActive = user.is_active ? true : false;
    }
}
