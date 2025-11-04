// Testbench for 2-bit adder
module tb_adder_2bit;
    reg [1:0] a, b;
    wire [1:0] sum;
    wire carry_out;
    integer passed, total;
    integer expected_sum, expected_carry;
    
    adder_2bit dut(
        .a(a),
        .b(b),
        .sum(sum),
        .carry_out(carry_out)
    );
    
    initial begin
        passed = 0;
        total = 0;
        
        $display("Testing 2-bit Adder");
        $display("-------------------");
        
        // Test case 1: 0 + 0
        a = 2'b00; b = 2'b00; #10;
        expected_sum = 0; expected_carry = 0;
        total = total + 1;
        if (sum == expected_sum && carry_out == expected_carry) begin
            $display("PASS: 0 + 0 = %0d (carry=%b)", sum, carry_out);
            passed = passed + 1;
        end else begin
            $display("FAIL: 0 + 0, expected sum=%0d carry=%b, got sum=%0d carry=%b", 
                     expected_sum, expected_carry, sum, carry_out);
        end
        
        // Test case 2: 1 + 1
        a = 2'b01; b = 2'b01; #10;
        expected_sum = 2; expected_carry = 0;
        total = total + 1;
        if (sum == expected_sum && carry_out == expected_carry) begin
            $display("PASS: 1 + 1 = %0d (carry=%b)", sum, carry_out);
            passed = passed + 1;
        end else begin
            $display("FAIL: 1 + 1, expected sum=%0d carry=%b, got sum=%0d carry=%b", 
                     expected_sum, expected_carry, sum, carry_out);
        end
        
        // Test case 3: 3 + 2 (overflow)
        a = 2'b11; b = 2'b10; #10;
        expected_sum = 1; expected_carry = 1;
        total = total + 1;
        if (sum == expected_sum && carry_out == expected_carry) begin
            $display("PASS: 3 + 2 = %0d (carry=%b)", sum, carry_out);
            passed = passed + 1;
        end else begin
            $display("FAIL: 3 + 2, expected sum=%0d carry=%b, got sum=%0d carry=%b", 
                     expected_sum, expected_carry, sum, carry_out);
        end
        
        // Test case 4: 3 + 3 (maximum)
        a = 2'b11; b = 2'b11; #10;
        expected_sum = 2; expected_carry = 1;
        total = total + 1;
        if (sum == expected_sum && carry_out == expected_carry) begin
            $display("PASS: 3 + 3 = %0d (carry=%b)", sum, carry_out);
            passed = passed + 1;
        end else begin
            $display("FAIL: 3 + 3, expected sum=%0d carry=%b, got sum=%0d carry=%b", 
                     expected_sum, expected_carry, sum, carry_out);
        end
        
        $display("\n%0d/%0d tests passed", passed, total);
        if (passed == total) $display("ALL TESTS PASSED");
        
        $finish;
    end
endmodule

