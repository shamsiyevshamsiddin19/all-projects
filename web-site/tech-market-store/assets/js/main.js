document.addEventListener('DOMContentLoaded', () => {
    // Basic interaction for category dropdowns
    const subCategories = document.querySelectorAll('.has-children > a');
    
    subCategories.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const parent = item.parentElement;
            parent.classList.toggle('active');
        });
    });

    // Back to top button
    const scrollTopBtn = document.querySelector('.scroll-top');
    if (scrollTopBtn) {
        scrollTopBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Carousel dots interaction
    const carousels = document.querySelectorAll('.carousel-dots');
    carousels.forEach(carousel => {
        const dots = carousel.querySelectorAll('.dot');
        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => {
                // Remove active from all
                dots.forEach(d => d.classList.remove('active'));
                // Add to clicked
                dot.classList.add('active');
                
                // Here we would typically slide the actual carousel items
            });
        });
    });
});
