export interface Order {
  id: number;
  customer: string;
  status: 'new' | 'review' | 'approved' | 'rejected';
  items: number;
  note: string;
}

export const ORDERS: Order[] = [
  { id: 4101, customer: 'Northwind Traders', status: 'new', items: 12, note: 'Needs a second check of the prices.' },
  { id: 4102, customer: 'Contoso Ltd', status: 'review', items: 3, note: 'Waiting for the customer to confirm.' },
  { id: 4103, customer: 'Fabrikam', status: 'approved', items: 7, note: 'Approved by the account manager.' },
  { id: 4104, customer: 'Tailspin Toys', status: 'rejected', items: 1, note: 'Duplicate of order 4099.' },
];
