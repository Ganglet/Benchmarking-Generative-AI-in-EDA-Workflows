// Testbench for AND gate
module tb_and_gate;
    reg a, b;
    wire y;
    integer passed, total;
    
    and_gate dut(
        .a(a),
        .b(b),
        .y(y)
    );
    
    initial begin
        passed = 0;
        total = 0;
        
        // Test all input combinations
        a = 0; b = 0; #10;
        total = total + 1;
        if (y == 0) begin
            $display("PASS: a=0, b=0, y=0");
            passed = passed + 1;
        end else begin
            $display("FAIL: a=0, b=0, expected y=0, got y=%b", y);
        end
        
        a = 0; b = 1; #10;
        total = total + 1;
        if (y == 0) begin
            $display("PASS: a=0, b=1, y=0");
            passed = passed + 1;
        end else begin
            $display("FAIL: a=0, b=1, expected y=0, got y=%b", y);
        end
        
        a = 1; b = 0; #10;
        total = total + 1;
        if (y == 0) begin
            $display("PASS: a=1, b=0, y=0");
            passed = passed + 1;
        end else begin
            $display("FAIL: a=1, b=0, expected y=0, got y=%b", y);
        end
        
        a = 1; b = 1; #10;
        total = total + 1;
        if (y == 1) begin
            $display("PASS: a=1, b=1, y=1");
            passed = passed + 1;
        end else begin
            $display("FAIL: a=1, b=1, expected y=1, got y=%b", y);
        end
        
        $display("\n%0d/%0d tests passed", passed, total);
        
        if (passed == total) begin
            $display("ALL TESTS PASSED");
        end else begin
            $display("SOME TESTS FAILED");
        end
        
        $finish;
    end
endmodule

