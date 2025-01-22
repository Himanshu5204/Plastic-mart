$(document).ready(function () {
     
    $('.payWithRazorpay').click(function (e) {
        e.preventDefault();

        var country = $("[name='country']").val();
        var fname = $("[name='fname']").val();
        var lname = $("[name='lname']").val();
        var address = $("[name='address']").val();
        var city = $("[name='city']").val();
        var state = $("[name='state']").val();
        var pincode = $("[name='pincode']").val();
        var email = $("[name='email']").val();
        var phone = $("[name='phone']").val();
        var token = $("[name = 'csrfmiddlewaretoken']").val();

        if(country == "" || fname == "" || lname == "" || address == "" || city == "" || state == "" || pincode == "" || email == ""  || phone == "")
        {
            swal("Alert!", "All fields are mandatory!", "warning");
            return false;
        }
        else
        {
            $.ajax({
                method:"GET",
                url:"/proceed_to_pay",
                success: function(response) {
                    // console.long(response);
                    var options = {
                        "key": "rzp_test_s65sX6z4b771Xc", // Enter the Key ID generated from the Dashboard
                        "amount": response.total_price * 100,//response.total_price * 100, // Amount is in currency subunits. Default currency is INR. Hence, 50000 refers to 50000 paise
                        "currency": "INR",
                        "name": "Plastic Mart",
                        "description": "Thank you for buying for us",
                        "image": "https://example.com/your_logo",
                        // "order_id": "order_IluGWxBm9U8zJ8", //This is a sample Order ID. Pass the id obtained in the response of Step 1
                        "handler": function (responseb){
                            alert(responseb.razorpay_payment_id);
                            data={
                                "fname": fname,
                                "lname": lname,
                                "address": address,
                                "city": city,
                                "state": state,
                                "pincode": pincode,
                                "email": email,
                                "phone": phone,
                                "payment_mode": "Paid by  Razorpay",
                                "payment_id": responseb.razorpay_payment_id,
                                csrfmiddlewaretoken: token
                            }
                            $.ajax({   
                                type: "POST",
                                url: "/placeorder/",
                                data: data,
                                success: function(responsec) {
                                    swal("Congratulations!!", responsec.status, "success").then((value) => {
                                        window.location.href = '/my_orders';
                                    });
                                },
                                error: function(xhr, status, error) {
                                    console.error("AJAX Error:", error);
                                    swal("Oops!", "An error occurred while placing the order. Please try again later.", "error");
                                }
                            });
                            
                        },
                        "prefill": {
                            "name": fname+" "+lname,
                            "email": email,
                            "contact": phone
                        },
                        "theme": {
                            "color": "#3399cc"
                        }
                    };
                    var rzp1 = new Razorpay(options);
                    rzp1.open();
                }
            });
        }
    });
});
