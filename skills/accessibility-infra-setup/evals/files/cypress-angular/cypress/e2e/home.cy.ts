describe('home page', () => {
  it('shows the expected heading', () => {
    cy.visit('/');
    cy.get('h1').should('be.visible');
  });
});
