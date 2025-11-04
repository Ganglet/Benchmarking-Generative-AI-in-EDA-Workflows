// Testbench for D flip-flop
module tb_d_flipflop;
    reg clk, rst, d;
    wire q;
    integer passed, total;
    
    d_flipflop dut(
        .clk(clk),
        .rst(rst),
        .d(d),
        .q(q)
    );
    
    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end
    
    initial begin
        passed = 0;
        total = 0;
        
        $display("Testing D Flip-Flop");
        $display("-------------------");
        
        // Test reset
        rst = 1; d = 1; #10;
        total = total + 1;
        if (q == 0) begin
            $display("PASS: Reset works, q=0");
            passed = passed + 1;
        end else begin
            $display("FAIL: Reset, expected q=0, got q=%b", q);
        end
        
        // Release reset, capture d=1
        rst = 0; d = 1; #10;
        total = total + 1;
        if (q == 1) begin
            $display("PASS: Captured d=1, q=1");
            passed = passed + 1;
        end else begin
            $display("FAIL: d=1, expected q=1, got q=%b", q);
        end
        
        // Change to d=0
        d = 0; #10;
        total = total + 1;
        if (q == 0) begin
            $display("PASS: Captured d=0, q=0");
            passed = passed + 1;
        end else begin
            $display("FAIL: d=0, expected q=0, got q=%b", q);
        end
        
        // Test that q holds when d changes mid-cycle
        d = 1; #3;  // Change d before clock edge
        d = 0; #7;  // Should capture 0
        total = total + 1;
        if (q == 0) begin
            $display("PASS: Captured correct value on clock edge");
            passed = passed + 1;
        end else begin
            $display("FAIL: Edge capture failed");
        end
        
        $display("\n%0d/%0d tests passed", passed, total);
        if (passed == total) $display("ALL TESTS PASSED");
        
        #10 $finish;
    end
endmodule

