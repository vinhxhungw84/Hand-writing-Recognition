`timescale 1ns/1ps

module pll_sdram_v_tb();

reg clk50, rst_n;
wire clk100, clk25, clk24, locked;

// --- Instantiate DUT (Device Under Test) ---
pll_sdram_v pll_for_sdram_0 (
    .rst       ( !rst_n ),
    .refclk    ( clk50 ),
    .outclk_0  ( clk100 ),   // expected: 100 MHz
    .outclk_2  ( clk25 ),    // expected: 25 MHz
    .outclk_3  ( clk24 ),    // expected: 24 MHz
    .locked    ( locked )
);

// --- Clock Generation (50 MHz) ---
// period = 20 ns -> 50 MHz
initial begin
    clk50 = 1'b0;
    forever #10 clk50 = ~clk50;
end

// --- Test Sequence ---
initial begin
    // Khởi tạo
    rst_n = 1'b0;

    // Reset giữ trong 100 ns
    #100;
    rst_n = 1'b1;

    // Đợi PLL lock
    wait(locked == 1'b1);
    $display("[%0t ns] PLL locked!", $time);

    // Quan sát thêm một thời gian để xem các clock chạy
    #1000;

    // Kết thúc mô phỏng
    $display("[%0t ns] Simulation finished.", $time);
    $stop;
end

endmodule
