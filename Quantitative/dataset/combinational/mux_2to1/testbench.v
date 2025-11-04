// Testbench for 2-to-1 MUX
module tb_mux_2to1;
    reg d0, d1, sel;
    wire y;
    integer passed, total;
    
    mux_2to1 dut(
        .d0(d0),
        .d1(d1),
        .sel(sel),
        .y(y)
    );
    
    initial begin
        passed = 0;
        total = 0;
        
        $display("Testing 2-to-1 MUX");
        $display("------------------");
        
        // Test sel=0, should select d0
        d0 = 0; d1 = 0; sel = 0; #10;
        total = total + 1;
        if (y == d0) begin
            $display("PASS: sel=0, d0=%b, d1=%b, y=%b", d0, d1, y);
            passed = passed + 1;
        end else begin
            $display("FAIL: sel=0, d0=%b, d1=%b, expected y=%b, got y=%b", d0, d1, d0, y);
        end
        
        d0 = 1; d1 = 0; sel = 0; #10;
        total = total + 1;
        if (y == d0) begin
            $display("PASS: sel=0, d0=%b, d1=%b, y=%b", d0, d1, y);
            passed = passed + 1;
        end else begin
            $display("FAIL: sel=0, d0=%b, d1=%b, expected y=%b, got y=%b", d0, d1, d0, y);
        end
        
        // Test sel=1, should select d1
        d0 = 0; d1 = 1; sel = 1; #10;
        total = total + 1;
        if (y == d1) begin
            $display("PASS: sel=1, d0=%b, d1=%b, y=%b", d0, d1, y);
            passed = passed + 1;
        end else begin
            $display("FAIL: sel=1, d0=%b, d1=%b, expected y=%b, got y=%b", d0, d1, d1, y);
        end
        
        d0 = 1; d1 = 0; sel = 1; #10;
        total = total + 1;
        if (y == d1) begin
            $display("PASS: sel=1, d0=%b, d1=%b, y=%b", d0, d1, y);
            passed = passed + 1;
        end else begin
            $display("FAIL: sel=1, d0=%b, d1=%b, expected y=%b, got y=%b", d0, d1, d1, y);
        end
        
        $display("\n%0d/%0d tests passed", passed, total);
        if (passed == total) $display("ALL TESTS PASSED");
        
        $finish;
    end
endmodule

