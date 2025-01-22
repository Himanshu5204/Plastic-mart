// checkout.js

$(document).ready(function() {
    // Function to update checkout page
    function updateCheckoutPage() {
        $.ajax({
            url: '/cart/',  // URL to fetch cart data
            type: 'GET',
            success: function(data) {
                // Update total, quantity, tax, and grand total on the checkout page
                $('#total').text(data.total);
                $('#quantity').text(data.quantity);
                $('#tax').text(data.tax);
                $('#grand_total').text(data.grand_total);

                // Update cart items table
                var cartItemsHtml = '';
                data.cart_items.forEach(function(cartItem) {
                    cartItemsHtml += '<tr>';
                    cartItemsHtml += '<td>' + cartItem.product.p_name + ' <strong class="mx-2">x</strong> ' + cartItem.quantity + '</td>';
                    cartItemsHtml += '<td>' + cartItem.sub_total + '</td>';
                    cartItemsHtml += '</tr>';
                });
                $('#cart_items_table tbody').html(cartItemsHtml);
            },
            error: function(xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText); // Log error message
            }
        });
    }

    // Call the updateCheckoutPage function on page load
    updateCheckoutPage();
});
