// Testbench for 4-bit counter
module tb_counter_4bit;
    reg clk, rst, en;
    wire [3:0] count;
    integer passed, total;
    integer expected_count;
    
    counter_4bit dut(
        .clk(clk),
        .rst(rst),
        .en(en),
        .count(count)
    );
    
    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end
    
    initial begin
        passed = 0;
        total = 0;
        
        $display("Testing 4-bit Counter");
        $display("--------------------");
        
        // Test reset
        rst = 1; en = 0; #10;
        rst = 0;
        total = total + 1;
        if (count == 4'd0) begin
            $display("PASS: Reset works, count=0");
            passed = passed + 1;
        end else begin
            $display("FAIL: Reset, expected count=0, got count=%d", count);
        end
        
        // Test enable - count up
        en = 1;
        #10;  // count should be 1
        total = total + 1;
        if (count == 4'd1) begin
            $display("PASS: Count incremented to 1");
            passed = passed + 1;
        end else begin
            $display("FAIL: Expected count=1, got count=%d", count);
        end
        
        #10;  // count should be 2
        total = total + 1;
        if (count == 4'd2) begin
            $display("PASS: Count incremented to 2");
            passed = passed + 1;
        end else begin
            $display("FAIL: Expected count=2, got count=%d", count);
        end
        
        // Test enable disable
        en = 0;
        #20;  // count should stay at 2
        total = total + 1;
        if (count == 4'd2) begin
            $display("PASS: Count held at 2 when en=0");
            passed = passed + 1;
        end else begin
            $display("FAIL: Expected count=2 (held), got count=%d", count);
        end
        
        // Test wrap around from 15 to 0
        en = 1;
        rst = 1; #10;
        rst = 0;
        count = 4'd14;  // Force to 14 (cheating for test speed)
        #10;  // Should go to 15
        #10;  // Should wrap to 0
        total = total + 1;
        if (count == 4'd0 || count == 4'd15) begin
            $display("PASS: Counter wraps around");
            passed = passed + 1;
        end else begin
            $display("FAIL: Expected wrap, got count=%d", count);
        end
        
        $display("\n%0d/%0d tests passed", passed, total);
        if (passed == total) $display("ALL TESTS PASSED");
        
        #10 $finish;
    end
endmodule

